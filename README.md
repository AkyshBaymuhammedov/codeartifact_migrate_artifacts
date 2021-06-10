# CodeArtifact package migration script

Can be used to copy artifacts (cross-region/same-region) between CodeArtifact repositories.
Repositories can be in different or same region, domain, domain owner.

# Prerequisities

[AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) needs to be installed and configured and **Boto3**, **json** and **requests** packages must be installed.  
   
`pip install boto`  
`pip install json`  
`pip install requests`  

# How to use

`codeartifact_copy_artifacts.py --sd <source-domain> --dd <destionation-domain> --sdo <source-domain-owner> --ddo <destionation-domain-owner> --sr <source-repository> --dr <destination-repository> --srg <source-region> --drg <destination-region>`
