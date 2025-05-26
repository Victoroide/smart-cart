from django.utils import timezone
from django.db.models import Count, Q
from django.db import transaction, IntegrityError
from app.orders.models import Order, Delivery, DeliveryAddress
from app.parameter.models import Country, State, City
from app.authentication.models import User, DeliveryProfile, DeliveryAssignment
import logging

logger = logging.getLogger(__name__)

def get_available_delivery_person():
    logger.debug("Attempting to find an available delivery person.")
    
    available_profiles = DeliveryProfile.objects.filter(status='available')
    if not available_profiles.exists():
        logger.warning("No delivery profiles found with status 'available'.")
        return None
        
    delivery_users = User.objects.filter(
        role='delivery',
        active=True,
        delivery_profile__in=available_profiles
    ).annotate(
        active_assignments_count=Count('delivery_assignments', 
            filter=Q(delivery_assignments__status__in=['assigned', 'in_progress'])
        )
    ).order_by('active_assignments_count')
    
    delivery_person = delivery_users.first()
    if delivery_person:
        logger.info(f"Available delivery person found: {delivery_person.email} (Assignments: {delivery_person.active_assignments_count})")
    else:
        logger.warning("No active delivery users found with available profiles and capacity.")
    return delivery_person

@transaction.atomic
def assign_delivery_person(delivery_instance: Delivery):
    logger.info(f"Attempting to assign delivery person for Delivery linked to Order ID: {delivery_instance.order_id}")

    if not isinstance(delivery_instance, Delivery):
        logger.error(f"Invalid type passed to assign_delivery_person. Expected Delivery, got {type(delivery_instance)}")
        return None
        
    if hasattr(delivery_instance, 'assignment') and delivery_instance.assignment:
        logger.info(f"Delivery for Order ID: {delivery_instance.order_id} already has an assignment to {delivery_instance.assignment.delivery_person.email}.")
        return delivery_instance.assignment
        
    delivery_person = get_available_delivery_person()
    
    if not delivery_person:
        logger.warning(f"No available delivery person found for Order ID: {delivery_instance.order_id}.")
        delivery_instance.delivery_status = 'pending_assignment'
        delivery_instance.delivery_notes = "No delivery person available at this time."
        delivery_instance.save(update_fields=['delivery_status', 'delivery_notes'])
        logger.info(f"Delivery status for Order ID: {delivery_instance.order_id} updated to 'pending_assignment'.")
        return None
        
    try:
        assignment = DeliveryAssignment.objects.create(
            delivery=delivery_instance,
            delivery_person=delivery_person,
            status='assigned'
        )
        logger.info(f"DeliveryAssignment ID: {assignment.id} created for Order ID: {delivery_instance.order_id}, assigned to {delivery_person.email}.")
        
        delivery_instance.delivery_status = 'assigned'
        delivery_instance.save(update_fields=['delivery_status'])
        logger.info(f"Delivery status for Order ID: {delivery_instance.order_id} updated to 'assigned'.")
        
        if hasattr(delivery_person, 'delivery_profile') and delivery_person.delivery_profile:
            profile = delivery_person.delivery_profile
            profile.status = 'busy'
            profile.save(update_fields=['status'])
            logger.info(f"DeliveryProfile status for {delivery_person.email} updated to 'busy'.")
        else:
            logger.warning(f"Delivery person {delivery_person.email} does not have a delivery_profile attribute or it's None.")
            
        return assignment
    except Exception as e:
        logger.error(f"Error creating DeliveryAssignment for Order ID: {delivery_instance.order_id}: {str(e)}", exc_info=True)
        delivery_instance.delivery_status = 'assignment_error'
        delivery_instance.delivery_notes = f"Error during assignment: {str(e)}"
        delivery_instance.save(update_fields=['delivery_status', 'delivery_notes'])
        return None

@transaction.atomic
def create_delivery_after_payment(order: Order):
    logger.info(f"Executing create_delivery_after_payment for Order ID: {order.id}")

    if not isinstance(order, Order):
        logger.error(f"Invalid type passed to create_delivery_after_payment. Expected Order, got {type(order)}")
        return None

    delivery_instance = None
    try:
        delivery_instance = Delivery.objects.get(order=order)
        logger.info(f"Existing Delivery found for Order ID: {order.id}. Current status: {delivery_instance.delivery_status}")
        if hasattr(delivery_instance, 'assignment') and delivery_instance.assignment:
            logger.info(f"Order ID: {order.id} already has a delivery with an assignment. No action needed.")
            return delivery_instance
    except Delivery.DoesNotExist:
        logger.info(f"No existing Delivery for Order ID: {order.id}. Creating new Delivery.")
        try:
            user = order.user
            address_details_kwargs = {}
            address_source_log = "No specific address found, attempting fallback."

            delivery_address_id = None
            if hasattr(order, 'metadata') and order.metadata and isinstance(order.metadata, dict):
                delivery_address_id = order.metadata.get('delivery_address_id')

            address_obj = None
            if delivery_address_id:
                try:
                    address_obj = DeliveryAddress.objects.get(id=delivery_address_id, user=user)
                    address_source_log = f"Using DeliveryAddress ID: {delivery_address_id} from order metadata."
                except DeliveryAddress.DoesNotExist:
                    logger.warning(f"DeliveryAddress ID: {delivery_address_id} from metadata not found for User ID: {user.id}.")
                    address_source_log = f"DeliveryAddress ID: {delivery_address_id} (metadata) not found."
            
            if not address_obj:
                address_obj = DeliveryAddress.objects.filter(user=user, is_default=True).first()
                if address_obj:
                    address_source_log = "Using user's default DeliveryAddress."
            
            if address_obj:
                address_details_kwargs = {
                    'recipient_name': address_obj.recipient_name,
                    'recipient_phone': address_obj.recipient_phone,
                    'address_line1': address_obj.address_line1,
                    'address_line2': address_obj.address_line2,
                    'city': address_obj.city,
                    'state': address_obj.state,
                    'country': address_obj.country,
                    'postal_code': address_obj.postal_code,
                }
            else:
                logger.warning(f"No DeliveryAddress found for User ID: {user.id} (metadata or default). Using fallback details.")
                address_source_log = "Using fallback: basic user info and default parameters."
                recipient_name_fallback = f"{user.first_name} {user.last_name}".strip() or user.email
                default_country = Country.objects.filter(is_active=True).first()
                default_state = State.objects.filter(country=default_country, is_active=True).first() if default_country else None
                default_city = City.objects.filter(state=default_state, is_active=True).first() if default_state else None

                if not default_city:
                    logger.error(f"Cannot create delivery for Order ID: {order.id}: Default Country/State/City parameters not found for fallback.")
                    return None
                
                address_details_kwargs = {
                    'recipient_name': recipient_name_fallback,
                    'recipient_phone': user.phone or "N/A",
                    'address_line1': "Address to be confirmed",
                    'city': default_city,
                    'state': default_state,
                    'country': default_country,
                    'postal_code': "N/A",
                    'delivery_notes': "User must confirm delivery address. " + address_source_log
                }

            delivery_instance = Delivery.objects.create(
                order=order,
                delivery_status='pending',
                estimated_arrival=timezone.now().date() + timezone.timedelta(days=3),
                **address_details_kwargs
            )
            logger.info(f"New Delivery created for Order ID: {order.id}. PK: {delivery_instance.order_id}. Source: {address_source_log}")

        except IntegrityError:
            logger.warning(f"IntegrityError while creating Delivery for Order ID: {order.id}. Attempting to re-fetch.")
            try:
                delivery_instance = Delivery.objects.get(order=order)
                logger.info(f"Successfully re-fetched Delivery for Order ID: {order.id} after IntegrityError.")
            except Delivery.DoesNotExist:
                logger.error(f"Delivery.DoesNotExist after IntegrityError for Order ID: {order.id}. This should not happen.")
                return None
        except Exception as e:
            logger.error(f"Error creating new Delivery object for Order ID: {order.id}: {str(e)}", exc_info=True)
            return None
    except Exception as e:
        logger.error(f"Unexpected error when trying to get/create Delivery for Order ID: {order.id}: {str(e)}", exc_info=True)
        return None

    if not delivery_instance:
        logger.error(f"Delivery instance is None for Order ID: {order.id} before attempting assignment. Cannot proceed.")
        return None

    logger.info(f"Proceeding to assign_delivery_person for Delivery (Order ID: {delivery_instance.order_id})")
    assign_delivery_person(delivery_instance)
    
    try:
        final_delivery_instance = Delivery.objects.get(order_id=delivery_instance.order_id)
        logger.info(f"Final state for Delivery (Order ID: {order.id}): Status='{final_delivery_instance.delivery_status}', Assignment present: {hasattr(final_delivery_instance, 'assignment') and final_delivery_instance.assignment is not None}")
        return final_delivery_instance
    except Delivery.DoesNotExist:
        logger.error(f"Delivery for Order ID {order.id} disappeared after assignment attempt. This is highly unusual.")
        return None
