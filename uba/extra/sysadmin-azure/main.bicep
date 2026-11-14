// ============================================================
// UBA on Azure — infrastructure as code (Bicep)
// ============================================================
// A TEACHING TEMPLATE. It provisions the core managed services UBA needs and
// deploys the backend as a Container App. Read it top to bottom: each resource
// is the Azure equivalent of one box in docker-compose.yml.
//
// Deploy with provision.sh (which supplies the image reference and secrets).
// NOTICE: API versions move quickly — if a deploy complains, update the
// `@yyyy-mm-dd` on that resource to a current one (`az provider show`).

@description('Where to create everything. Cheap + close to the Caribbean.')
param location string = 'eastus'

@description('Short name stem for resources; must be globally unique-ish.')
param namePrefix string = 'uba'

@description('Postgres admin login.')
param dbAdmin string = 'ubaadmin'

@description('Postgres admin password. Supplied at deploy time, never hardcoded.')
@secure()
param dbPassword string

@description('Full image reference, e.g. ubaacr.azurecr.io/uba-backend:1.0.0')
param backendImage string

@description('A long random value for signing login tokens.')
@secure()
param jwtSecret string

var dbName = 'uba'

// ---------- logging: everything's logs land here ----------
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ---------- container registry: stores the images we build ----------
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${namePrefix}acr${uniqueString(resourceGroup().id)}'
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: true } // demo convenience; prefer managed identity in prod
}

// ---------- secrets store: the real home for passwords ----------
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
  }
}

// ---------- managed PostgreSQL (replaces the postgres container) ----------
resource db 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: '${namePrefix}-pg-${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_B1ms' // burstable, the cheapest tier — fine for a demo
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: dbAdmin
    administratorLoginPassword: dbPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' } // enable for production
  }

  resource database 'databases@2023-12-01-preview' = {
    name: dbName
  }

  // Demo firewall: allow other Azure services in. Production uses a private VNet.
  resource allowAzure 'firewallRules@2023-12-01-preview' = {
    name: 'AllowAllAzureServices'
    properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
  }
}

// ---------- Container Apps environment (the place apps run) ----------
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

// ---------- the backend, as a Container App ----------
resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-backend'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      // public HTTPS endpoint, TLS handled by Azure (this is our Traefik ingress)
      ingress: { external: true, targetPort: 8000, transport: 'auto' }
      registries: [
        { server: acr.properties.loginServer, username: acr.name, passwordSecretRef: 'acr-pwd' }
      ]
      // secrets are referenced by name below, never written in plain text
      secrets: [
        { name: 'acr-pwd', value: acr.listCredentials().passwords[0].value }
        { name: 'db-url', value: 'postgresql+psycopg://${dbAdmin}:${dbPassword}@${db.properties.fullyQualifiedDomainName}:5432/${dbName}' }
        { name: 'jwt', value: jwtSecret }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'UBA_ENVIRONMENT', value: 'production' }
            { name: 'UBA_DATABASE_URL', secretRef: 'db-url' }
            { name: 'UBA_JWT_SECRET', secretRef: 'jwt' }
            { name: 'UBA_COOKIE_SECURE', value: 'true' } // HTTPS only in the cloud
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 } // Container Apps autoscales for us
    }
  }
}

output backendUrl string = 'https://${backend.properties.configuration.ingress.fqdn}'
output registryLoginServer string = acr.properties.loginServer
output postgresHost string = db.properties.fullyQualifiedDomainName
