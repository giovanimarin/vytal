variable "project_id" { type = string }
variable "region"     { type = string }
variable "env"        { type = string }
variable "image"      { type = string }

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "secret_vars" {
  description = "Mapa de nome_var => secret_id no Secret Manager"
  type        = map(string)
  default     = {}
}
