terraform {
  required_version = ">= 0.11"
}

provider "archive" {}

provider "aws" {
  region = "us-east-1"
}
