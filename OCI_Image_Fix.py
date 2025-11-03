# coding: utf-8

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# name: OCI_Image_Fix.py
#
# Author: Florian Bonneville
# Version: 2.0.0 - Nov 3rd, 2025
#
# Disclaimer: 
# This script is an independent tool developed by 
# Florian Bonneville and is not affiliated with or 
# supported by Oracle. It is provided as-is and without 
# any warranty or official endorsement from Oracle
#
# reference: 
# https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/configuringimagecapabilities.htm
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -

version="2.0.0"

import os
import oci
import time
from datetime import datetime
from modules.utils import clear, path_expander, print_info, check_folder, init_csv_report, check_file_size, format_duration
from modules.compute import get_schema, image_fix
from modules.identity import init_authentication, validate_region_connectivity, get_home_region, get_region_subscription_list, get_compartment_list, check_bucket, upload_file
from modules.arguments import get_cmd_arguments, get_missing_arguments
from modules.search import search_images, set_search_query

script_version=version
script_path=os.path.abspath(__file__)
script_name=(os.path.basename(script_path))[:-3]

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -
clear()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Load command line arguments
# - - - - - - - - - - - - - - - - - - - - - - - - - -
args=get_cmd_arguments()
args=get_missing_arguments(args)
args_dict=vars(args)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Init OCI authentication
# - - - - - - - - - - - - - - - - - - - - - - - - - -
config, signer, tenancy, auth_name, details=init_authentication(
     args.user_auth, 
     args.config_file_path, 
     args.config_profile
     )

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Clear shell screen in case of authentication errors
# - - - - - - - - - - - - - - - - - - - - - - - - - -
clear()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Start printing script info
# - - - - - - - - - - - - - - - - - - - - - - - - - -
print(green(f"\n{'*'*94:94}"))
print_info(green, "Script", "started", script_name)
print_info(green, "Script", "version", script_version)
print_info(green, "Script", "action", "dry run" if args.dryrun else "fix images")
print_info(green, "Login", "success", auth_name)
print_info(green, "Login", "profile", details.lower())
print_info(green, "Tenancy", "name", tenancy.name)
print_info(green, "Region", "home", tenancy.home_region_key)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Init oci service client
# - - - - - - - - - - - - - - - - - - - - - - - - - -
identity_client=oci.identity.IdentityClient(
     config=config, 
     signer=signer
     )
search_client=oci.resource_search.ResourceSearchClient(
     config=config,
     signer=signer
     )
obj_storage_client=oci.object_storage.ObjectStorageClient(
     config=config,
     signer=signer
     )
tenancy_id=config["tenancy"]

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Set target region(s)
# - - - - - - - - - - - - - - - - - - - - - - - - - -
regions_to_analyze=get_region_subscription_list(
     identity_client,
     tenancy_id,
     args.target_region
     )
regions_validated, region_errors=validate_region_connectivity(
     regions_to_analyze,
     config,
     signer
     )
home_region=get_home_region(
     identity_client, 
     tenancy_id
     )
print_info(green, "Region", "selected", len(regions_validated))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Set target compartment (root default)
# - - - - - - - - - - - - - - - - - - - - - - - - - -
top_level_compartment_id=args.target_comp or tenancy_id

my_compartments=get_compartment_list(
    identity_client, 
    top_level_compartment_id
    )

root_compartment_name=identity_client.get_compartment(top_level_compartment_id).data.name
print_info(green, "Compartment", "name", root_compartment_name)
print_info(green, "Compartment", "child", len(my_compartments))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# set csv report folder
# - - - - - - - - - - - - - - - - - - - - - - - - - -
report_folder = path_expander(args.report_folder if args.report_folder else './')
check_folder(report_folder, output=True)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# init csv report file
# - - - - - - - - - - - - - - - - - - - - - - - - - -
now = datetime.today().strftime('%Y%m%d_%H%M')
base_report_name = args.report_name if args.report_name else 'oci_custom_images'
full_report_name = f'{base_report_name}_{now}.csv'
csv_report = os.path.join(report_folder, full_report_name)
init_csv_report(csv_report)
print_info(green, 'Report', 'name', str(full_report_name[:32])+'...')

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check report bucket
# - - - - - - - - - - - - - - - - - - - - - - - - - -

if not args.noupload:
     report_bucket = args.report_bucket if args.report_bucket else 'oci_custom_images'

     bucket, bucket_comp, bucket_state = check_bucket(
          identity_client,
          search_client,
          obj_storage_client,
          top_level_compartment_id, 
          report_bucket,
          tenancy_id)
     
     if bucket_state:
          print_info(green, 'Report', 'bucket', bucket.name)
          print_info(green, 'Report', 'compartment', bucket_comp.name)
     else:
          args.noupload = True

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# End print script info
# - - - - - - - - - - - - - - - - - - - - - - - - - -
print_info(green, 'Report', 'location', 'local+cloud' if not args.noupload else 'local only')
print(green(f"{'*'*94:94}\n"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Start analysis
# - - - - - - - - - - - - - - - - - - - - - - - - - -
analysis_start=time.perf_counter()

# Iterate over regions
images_dict={}
for region in regions_validated:
     
     config["region"]=region.region_name
     identity_client=oci.identity.IdentityClient(config=config, signer=signer)
     core_client=oci.core.ComputeClient(config=config, signer=signer)

     # Retrieve schema_data and schema_version_name
     schema_data, schema_version_name=get_schema(core_client)

     # Init image counter per region
     total_images_count = 0

     if args.image_id:
          count=image_fix(
               identity_client,
               core_client,
               args.image_id,
               region,
               schema_data,
               schema_version_name,
               csv_report,
               args.dryrun
               )

          total_images_count = total_images_count + count
     else:
          # Construct a custom image search query based on the provided arguments
          images_query=set_search_query(args, my_compartments)

          # Search for custom images
          print(yellow(f"\r   => Searching for custom images in {region.region_name}" + "..."  + " " * 20),end="\r", flush=True)
          #print(" " * 150, end="\r")

          # Collect custom images in the region
          images=search_images(
               config,
               signer, 
               images_query
               )

          # Analyze each image found
          for image in images.data:
               count=image_fix(
                    identity_client,
                    core_client,
                    image.identifier,
                    region,
                    schema_data,
                    schema_version_name,
                    csv_report,
                    args.dryrun
                    )

               total_images_count = total_images_count + count

     # Record image count in the region
     images_dict[region.region_name]=total_images_count

print(" " * 150, end="\r")

print(green("\nREPORT SUMMARY:"))
if not check_file_size(csv_report, 230) == False:
     print(green(f"{'  - Path:':<25} {report_folder[:100]}"))
     print(green(f"{'  - File:':<25} {full_report_name}"))
     file_size, file_control = check_file_size(csv_report, 230)
     print(green(f"{'  - Size:':<25} {file_size}"))

     if not args.noupload:
          upload_file(
               obj_storage_client,
               bucket.name,
               csv_report,
               full_report_name,
               tenancy_id)

          print(green(f"{'  - Tenancy:':<25} {tenancy.name}"))
          print(green(f"{'  - Region:':<25} {tenancy.home_region_key}"))
          print(green(f"{'  - Compartment:':<25} {bucket_comp.name}"))
          print(green(f"{'  - Bucket:':<25} {bucket.name}"))

# Sort regions dict
images_dict = {k: images_dict[k] for k in sorted(images_dict)}

def check_dict(dict):
    return False if all(v == 0 for v in dict.values()) else True

if check_dict(images_dict):
     print(green(f"{'  - Custom images:':<25} {sum(images_dict.values())}"))
     for region, count in images_dict.items():
          if count > 0:
               print(green(f"{'    * ' + region + ':':<25} {count}"))

else:
     print(green(f"  - No custom images analyzed"))

analysis_end=time.perf_counter()
execution_time=analysis_end - analysis_start
print(green(f"{'  - Execution time:':<25} {format_duration(execution_time)}\n"))