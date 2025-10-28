# coding: utf-8

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# name: OCI_Image_Fix.py
#
# Author: Florian Bonneville
# Version: 1.0.0 - Oct 28th, 2025
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

version="1.0.0"

import os
import oci
import time
from datetime import datetime
from modules.utils import *
from modules.identity import *
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
     signer=signer)

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
# End print script info
# - - - - - - - - - - - - - - - - - - - - - - - - - -
print(green(f"{'*'*94:94}\n"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Start analysis
# - - - - - - - - - - - - - - - - - - - - - - - - - -
analysis_start=time.perf_counter()

# Iterate over regions
for region in regions_validated:

     config["region"]=region.region_name

     identity_client=oci.identity.IdentityClient(config=config, signer=signer)
     core_client=oci.core.ComputeClient(config=config, signer=signer)

     # Construct a custom image search query based on the provided arguments
     images_query=set_search_query(args, my_compartments)

     # Search for custom images
     print(yellow(f"\r   => Searching for custom images in {region.region_name}" + "..."  + " " * 20),end="\r", flush=True)
     #print(" " * 150, end="\r")

     images=search_images(
          config,
          signer, 
          images_query
          )

     capabilities=core_client.list_compute_image_capability_schemas().data

     for item in capabilities:
          try:
               if isinstance(item.schema_data, dict):
                    compute_amd_secure_encryption=item.schema_data.get('Compute.AMD_SecureEncryptedVirtualization')
                    if compute_amd_secure_encryption.source == "IMAGE":
                         schema_data=item.schema_data
                         compute_global_image_capability_schema_version_name=item.compute_global_image_capability_schema_version_name
                         break
          except:
               pass

     # Process each custom image
     for image in images.data:
          print(yellow(f"\r   => Analyzing custom image: {image.display_name}" + "..."  + " " * 60),end="\r", flush=True)
          #print(" " * 150, end="\r")
          try:
               compartment_name=get_compartment_name(identity_client, image.compartment_id)
               image=core_client.get_image(image.identifier).data

               if image.lifecycle_state == "AVAILABLE":
                    capabilities=core_client.list_compute_image_capability_schemas(image_id=image.id).data

                    if capabilities == []:
                         print(cyan(f"FIXING IMAGE:"))
                         print(cyan(f"  name: {image.display_name}"))
                         print(cyan(f"  ocid: {image.id}"))
                         print(cyan(f"  compartment: {compartment_name}"))
                         print(cyan(f"  region: {region.region_name}"))

                         create_compute_image_capability_schema_response=core_client.create_compute_image_capability_schema(
                         create_compute_image_capability_schema_details=oci.core.models.CreateComputeImageCapabilitySchemaDetails(
                              compartment_id=image.compartment_id,
                              compute_global_image_capability_schema_version_name=compute_global_image_capability_schema_version_name,
                              image_id=image.id,
                              schema_data=schema_data
                                   )
                              )
                         # Check if capabilities have been added 
                         capabilities=core_client.list_compute_image_capability_schemas(image_id=image.id).data

                         if capabilities != []:
                              print(green("  update: completed\n"))
                         else:
                              print(red("  update: failed\n"))

          except Exception as e:
               if hasattr(e, "code") and hasattr(e, "message"):
                    print_error(e.code, e.message)
               else:
                    print_error(e)
               continue

print(" " * 100, end="\r")

analysis_end=time.perf_counter()
execution_time=analysis_end - analysis_start
print(green(f"\nExecution time: {format_duration(execution_time)}\n"))