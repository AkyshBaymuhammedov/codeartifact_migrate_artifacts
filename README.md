# CodeArtifact package migration script

Python script which can be used to copy artifacts (cross-region/same-region) between CodeArtifact repositories.
Repositories can be in different or same region, domain, domain owner.

# Prerequisities

**Boto3**, **json** and **requests** packages need to be installed.  
`pip install boto`  
`pip install json`  
`pip install requests`  

# How to use

`codeartifact_copy_artifacts.py --sd <source-domain> --dd <destionation-domain> --sdo <source-domain-owner> --ddo <destionation-domain-owner> --sr <source-repository> --dr <destination-repository> --srg <source-region> --drg <destination-region>`
