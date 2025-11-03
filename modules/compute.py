# coding: utf-8
import oci
from modules.identity import get_compartment_name
from modules.utils import cyan, green, yellow, red, write_to_csv

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Retriveve the schema data
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_schema(core_client):

     capabilities=core_client.list_compute_image_capability_schemas().data
     for item in capabilities:
          try:
               if isinstance(item.schema_data, dict):
                    compute_amd_secure_encryption=item.schema_data.get('Compute.AMD_SecureEncryptedVirtualization')
                    if compute_amd_secure_encryption.source == "IMAGE":
                         schema_data=item.schema_data
                         schema_version_name=item.compute_global_image_capability_schema_version_name
                         return schema_data, schema_version_name
          except:
               pass

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Apply schema data to image
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def image_fix(identity_client, core_client, image_id, region, schema_data, schema_version_name, csv_report, dryrun):

    count=0

    try:
        # Set strings ".region_name." and ".region_key."
        region_name, region_key = (f".{v.lower()}." for v in (region.region_name, region.region_key))

        image=core_client.get_image(image_id).data
        print(yellow(f"\r   => Analyzing [{region.region_key}] custom image: {image.display_name}" + "..."  + " " * 60),end="\r", flush=True)
        # sometimes search can return images from another region...
        if any(r in image.id for r in (region_name, region_key)):
            if image.lifecycle_state == "AVAILABLE":
                count=1
                capabilities=core_client.list_compute_image_capability_schemas(image_id=image.id).data
                compartment_name=get_compartment_name(identity_client, image.compartment_id)

                if capabilities == []:
                    print(" " * 200, end="\r")
                    print(cyan(f"\nFIXING IMAGE:"))
                    print(cyan(f"{'  - name:':<20} {image.display_name}"))
                    print(cyan(f"{'  - created on:':<20} {image.time_created.strftime('%Y-%m-%d')}"))
                    print(cyan(f"{'  - ocid:':<20} {image.id}"))
                    print(cyan(f"{'  - state:':<20} {image.lifecycle_state}"))
                    print(cyan(f"{'  - compartment:':<20} {compartment_name}"))
                    print(cyan(f"{'  - region:':<20} {region.region_name}"))

                    if dryrun == False:
                        create_compute_image_capability_schema_response=core_client.create_compute_image_capability_schema(
                        create_compute_image_capability_schema_details=oci.core.models.CreateComputeImageCapabilitySchemaDetails(
                            compartment_id=image.compartment_id,
                            compute_global_image_capability_schema_version_name=schema_version_name,
                            image_id=image.id,
                            schema_data=schema_data
                            )
                        )

                        # Check if capabilities have been added 
                        capabilities=core_client.list_compute_image_capability_schemas(image_id=image.id).data

                        if capabilities != []:
                            print(green(f"{'  - update:':<20} completed"))
                        else:
                            print(red(f"{'  - update:':<20} failed"))

                csv_data = {
                    'region_name': region.region_name,
                    'compartment_name': compartment_name,
                    'compartment_ocid': image.compartment_id,
                    'display_name': image.display_name,
                    'ocid': image.id,
                    'state': image.lifecycle_state,
                    'schema': 'true' if capabilities else 'false',
                    'base_image_id': image.base_image_id,
                    'billable_size_in_gbs': image.billable_size_in_gbs,
                    'launch_mode': image.launch_mode,
                    'operating_system': image.operating_system,
                    'operating_system_version': image.operating_system_version,
                    'size_in_mbs': image.size_in_mbs,
                    'created_on': image.time_created.strftime('%Y-%m-%d'),
                    'created_at': image.time_created.strftime('%H:%M:%S'),
                    'time_created': image.time_created,
                    }

                write_to_csv(csv_report, csv_data)

    except Exception as e:
        if hasattr(e, "code") and hasattr(e, "message"):
            print(red(f"{'  - image ocid:':<20} {image_id}"))
            print(red(f"{'  - error code:':<20} {e.code}"))
            print(red(f"{'  - error message:':<20} {e.message}"))
        else:
            print(red(f"{'  - image ocid:':<20} {image_id}"))
            print(red(f"{'  - error:':<20} {e}"))
     
    return count