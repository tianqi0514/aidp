export interface Project {
  id: string
  name: string
  slug: string
  description: string
  status: string
  timezone: string
  created_at: string
  updated_at: string
}

export interface Secret {
  id: string
  project_id: string
  name: string
  kind: string
  created_at: string
  updated_at: string
}

export interface ConnectorType {
  id: string
  name: string
  mode: string
  categories: string[]
  config_schema: Record<string, unknown>
  capabilities: string[]
}

export interface Catalog {
  id: string
  project_id: string
  name: string
  description: string
  connector_type: string
  secret_id: string | null
  config: Record<string, unknown>
  scope: string
  read_only: boolean
  status: string
  last_error: string | null
  last_checked_at: string | null
}

export interface DataResource {
  id: string
  project_id: string
  catalog_id: string
  external_id: string
  name: string
  namespace: string
  category: string
  status: string
  discovery_status: string
  schema: { fields?: Array<Record<string, unknown>>; primary_key?: string[] }
  governance: Record<string, unknown>
}

export interface KnowledgeNetwork {
  id: string
  project_id: string
  key: string
  name: string
  description: string
  version: number
  branch: string
  status: string
  concept_groups: Array<Record<string, unknown>>
}

export interface ObjectType {
  id: string
  network_id: string
  key: string
  name: string
  description: string
  source_resource_id: string | null
  properties: Array<Record<string, unknown>>
  primary_keys: string[]
  display_key: string | null
  incremental_key: string | null
  indexes: Array<Record<string, unknown>>
  status: string
}

export interface RelationType {
  id: string
  network_id: string
  key: string
  name: string
  source_object_type_id: string
  target_object_type_id: string
  cardinality: string
  mapping_type: string
}

export interface ActionType {
  id: string
  network_id: string
  key: string
  name: string
  operation: string
  object_type_id: string
  permission: string
  executor: Record<string, unknown>
}

export interface Capability {
  name: string
  module: string
  description: string
  risk: 'read' | 'write' | 'high'
  idempotent: boolean
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
}
