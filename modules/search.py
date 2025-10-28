# coding: utf-8

import oci
import inspect
from modules.utils import print_error
from datetime import datetime, timezone

custom_retry_strategy=oci.retry.RetryStrategyBuilder(
                                                        max_attempts_check=True,
                                                        max_attempts=10,
                                                        total_elapsed_time_check=True,
                                                        total_elapsed_time_seconds=600,
                                                        retry_max_wait_between_calls_seconds=45,#Max Wait: 45sec between attempts
                                                        retry_base_sleep_time_seconds=2,
                                                        service_error_check=True,
                                                        service_error_retry_on_any_5xx=True,
                                                        service_error_retry_config={
                                                                                    400: ["QuotaExceeded", "LimitExceeded"],
                                                                                    409: ["Conflict"],
                                                                                    429: [],
                                                                                    404: ["NotAuthorizedOrNotFound"]
                                                                                    },
                                                        backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE
                                                        ).get_retry_strategy()
# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Set search query with parameters
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def set_search_query(args, my_compartments):

    try:
        # init base query and conditions
        base_query=f"query image resources where ((lifeCycleState='AVAILABLE'))"
        
        conditions=[]

        # Add the compartment ocid in the search query if target_comp option is submitted 
        if args.target_comp:
            # Handle multiple compartments if the compartment has child compartments
            compartment_conditions=[f"compartmentId='{comp.id}'" for comp in my_compartments]
            # Wrap the multiple compartments with parentheses
            conditions.append(f"({' || '.join(compartment_conditions)})")

        # Final query construction
        instances_query=base_query
        if conditions:
            instances_query += " && " + " && ".join(conditions)

        return instances_query

    except Exception as e:
        function_name=inspect.currentframe().f_code.co_name
        if hasattr(e, "code") and hasattr(e, "message"):
            print_error(f"An error occurred in -- {function_name} --:", e.code, e.message)
        else:
            print_error(f"An error occurred in -- {function_name} --:", e)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run seach query
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def search_images(config, signer, query):

    search_client=oci.resource_search.ResourceSearchClient(config=config, signer=signer)
    
    try:        
        search_resource_details=oci.resource_search.models.StructuredSearchDetails(
            query=query,
            type="Structured",
            matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE)

        all_resources=oci.pagination.list_call_get_all_results(
            search_client.search_resources, 
            search_resource_details,
            )

        return all_resources
    
    except Exception as e:
        function_name=inspect.currentframe().f_code.co_name
        if hasattr(e, "code") and hasattr(e, "message"):
            print_error(f"An error occurred in -- {function_name} --:", query, e.code, e.message)
        else:
            print_error(f"An error occurred in -- {function_name} --:", query, e)
        raise SystemExit(1)