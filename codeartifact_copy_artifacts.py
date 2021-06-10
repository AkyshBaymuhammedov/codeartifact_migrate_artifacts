import boto3
import json
import io
import requests
import datetime
import sys, os
import getopt
import time
from requests.api import head
from botocore.config import Config

src_domain, dst_domain, src_domainOwner, dst_domainOwner, src_repository, dst_repository, format = ('',) * 7

def get_packages(client):
    response = client.list_packages(
        domain=src_domain,
        domainOwner=src_domainOwner,
        repository=src_repository,
        format=format,
        maxResults=1000
    )
    resp_dict = json.loads(str(response).replace("\'", "\""))
    return resp_dict.get("packages")


def get_package_versions(client, package):
    response = client.list_package_versions(
        domain=src_domain,
        domainOwner=src_domainOwner,
        repository=src_repository,
        namespace=package.get("namespace"),
        package=package.get("package"),
        format=format
    )
    versions_dict = json.loads(str(response).replace("\'", "\""))
    return versions_dict.get("versions")


def get_package_version_assets(client, package, version):
    response = client.list_package_version_assets(
        domain=src_domain,
        domainOwner=src_domainOwner,
        repository=src_repository,
        namespace=package.get("namespace"),
        package=package.get("package"),
        packageVersion=version.get("version"),
        format=format
    )
    assets_dict = json.loads(str(response).replace("\'", "\""))
    return assets_dict.get("assets")


def download_asset(client, package, version, asset):
    response = client.get_package_version_asset(
        domain=src_domain,
        domainOwner=src_domainOwner,
        repository=src_repository,
        format=format,
        namespace=package.get("namespace"),
        package=package.get("package"),
        packageVersion=version.get("version"),
        asset=asset.get("name"),
    )
    with io.FileIO(asset.get("name"), 'w') as file:
        for i in response['asset']._raw_stream:
            file.write(i)


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def get_authorization_token(client):
    response = client.get_authorization_token(
        domain=dst_domain,
        domainOwner=dst_domainOwner,
        durationSeconds=43200
    )
    converted_resp = json.dumps(response, default=myconverter)
    token_dict = json.loads(converted_resp)
    return token_dict.get("authorizationToken")


def update_package_status(client, package, version):
    response = client.update_package_versions_status(
        domain=dst_domain,
        domainOwner=dst_domainOwner,
        repository=dst_repository,
        format=format,
        namespace=package.get("namespace"),
        package=package.get("package"),
        versions=[version.get("version")],
        targetStatus='Published'
    )
    update_status_dict = json.loads(str(response).replace("\'", "\""))
    print("Update status: " + str(update_status_dict.get("ResponseMetadata").get("HTTPStatusCode")))


def get_repository_endpoint(client):
    response = client.get_repository_endpoint(
        domain=dst_domain,
        domainOwner=dst_domainOwner,
        repository=dst_repository,
        format=format
    )
    repo_dict = json.loads(str(response).replace("\'", "\""))
    return repo_dict.get("repositoryEndpoint")

def delete_downloaded_assets(assets):
    for asset in assets:
        os.remove(asset.get("name"))

def move_packages(source_client, target_client):
    all_assets = []
    packages = get_packages(source_client)
    print(len(packages))
    for package in packages:
        versions = get_package_versions(source_client, package)
        for version in versions:
            assets = get_package_version_assets(source_client, package, version)
            all_assets += assets
            for asset in assets:
                download_asset(source_client, package, version, asset)
                print(asset.get("name"))
                headers = {
                    'Content-Type': 'application/octet-stream'
                }
                namespace_url = package.get("namespace").replace(".", "/")
                url = get_repository_endpoint(target_client) + \
                    namespace_url+"/" + \
                    package.get("package")+"/" + \
                    version.get("version")+"/"+asset.get("name")
                response = requests.put(url, auth=("aws", get_authorization_token(target_client)), data=open(asset.get("name"), 'rb'), headers=headers)
                print("publish: "+response.text)
                update_package_status(target_client, package, version)
    time.sleep(5)
    delete_downloaded_assets(all_assets)

def print_help():
    print('codeartifact_copy_artifacts.py --sd <source-domain> --dd <destionation-domain> --sdo <source-domain-owner> --ddo <destionation-domain-owner> --sr <source-repository> --dr <destination-repository> --srg <source-region> --drg <destination-region>')
    sys.exit(2)

def main(argv):
    if(len(argv) < 9):
        print_help()

    src_region, dst_region = ('',)*2
    try:
        opts, args = getopt.getopt(argv, "h", ["sd=", "dd=", "sdo=", "ddo=", "sr=", "dr=", "srg=", "drg=", "f="])
    except getopt.GetoptError:
        print_help()
    for opt, arg in opts:
        if opt == '-h':
            print_help()
        elif opt == '--sd':
            global src_domain 
            src_domain = arg
        elif opt == '--dd':
            global dst_domain
            dst_domain = arg
        elif opt == '--sdo':
            global src_domainOwner
            src_domainOwner = arg
        elif opt == '--ddo':
            global dst_domainOwner
            dst_domainOwner = arg
        elif opt == '--sr':
            global src_repository
            src_repository = arg
        elif opt == '--dr':
            global dst_repository
            dst_repository = arg
        elif opt == '--srg':
            src_region = arg
        elif opt == '--drg':
            dst_region = arg
        elif opt == '--f':
            global format
            format = arg            

    source_config = Config(
        region_name=src_region,
        signature_version='v4',
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        }
    )

    target_config = Config(
        region_name=dst_region,
        signature_version='v4',
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        }
    )

    source_client = boto3.client('codeartifact', config=source_config)
    target_client = boto3.client('codeartifact', config=target_config)
    move_packages(source_client, target_client)

if __name__ == '__main__':
    main(sys.argv[1:])
