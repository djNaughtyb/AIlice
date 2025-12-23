"""Billing and payment endpoints with Stripe integration."""
import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, Subscription
from api.stripe_service import StripeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


# Pydantic schemas
class CheckoutRequest(BaseModel):
    """Request body for creating a checkout session."""
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Response for checkout session creation."""
    session_id: str
    url: str


class SubscriptionResponse(BaseModel):
    """Response for subscription details."""
    id: int
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    price: float = 49.99
    currency: str = "usd"

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Response for invoice details."""
    id: str
    amount_due: int
    amount_paid: int
    currency: str
    status: str
    created: str
    invoice_pdf: Optional[str] = None
    hosted_invoice_url: Optional[str] = None


# Endpoints
@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_200_OK)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription.
    
    This endpoint creates a Stripe checkout session that allows users to subscribe
    to the platform. The user will be redirected to Stripe's hosted checkout page.
    """
    try:
        # Check if user already has an active subscription
        existing_subscription = StripeService.get_subscription(db, current_user.id)
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )
        
        # Create or get Stripe customer
        customer_id = None
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        if subscriptions:
            customer_id = subscriptions.stripe_customer_id
        else:
            customer_id = StripeService.create_customer(current_user, current_user.email)
        
        # Create checkout session
        session_data = StripeService.create_checkout_session(
            customer_id=customer_id,
            user_id=current_user.id,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return CheckoutResponse(**session_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription details.
    
    Returns the active subscription information for the authenticated user.
    """
    subscription = StripeService.get_subscription(db, current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return SubscriptionResponse(
        id=subscription.id,
        status=subscription.status.value,
        current_period_start=subscription.current_period_start.isoformat(),
        current_period_end=subscription.current_period_end.isoformat(),
        cancel_at_period_end=subscription.cancel_at_period_end
    )


@router.post("/subscription/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    cancel_immediately: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel user's subscription.
    
    Args:
        cancel_immediately: If True, cancel immediately; otherwise cancel at period end
    """
    subscription = StripeService.get_subscription(db, current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    success = StripeService.cancel_subscription(
        db,
        subscription.stripe_subscription_id,
        cancel_immediately
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )
    
    return {
        "message": "Subscription canceled successfully",
        "cancel_immediately": cancel_immediately
    }


@router.post("/subscription/reactivate", status_code=status.HTTP_200_OK)
async def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reactivate a canceled subscription (before period end).
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.cancel_at_period_end == True
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription scheduled for cancellation found"
        )
    
    success = StripeService.reactivate_subscription(
        db,
        subscription.stripe_subscription_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription"
        )
    
    return {"message": "Subscription reactivated successfully"}


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's invoices.
    
    Args:
        limit: Maximum number of invoices to return (default: 10)
    """
    # Get customer ID from subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        return []
    
    invoices = StripeService.get_invoices(
        subscription.stripe_customer_id,
        limit
    )
    
    return [InvoiceResponse(**inv) for inv in invoices]


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint receives and processes webhook events from Stripe,
    including subscription updates, payment successes, and cancellations.
    """
    try:
        # Get webhook payload and signature
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Construct and verify event
        event = StripeService.construct_webhook_event(payload, sig_header)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        
        # Handle different event types
        event_type = event.type
        logger.info(f"Received Stripe webhook event: {event_type}")
        
        if event_type == "checkout.session.completed":
            # Payment successful, create subscription
            session = event.data.object
            user_id = int(session.metadata.get("user_id"))
            
            # Get subscription from Stripe
            import stripe
            subscription = stripe.Subscription.retrieve(session.subscription)
            
            # Create subscription record
            StripeService.create_subscription_record(db, user_id, subscription)
            logger.info(f"Created subscription for user {user_id}")
        
        elif event_type == "customer.subscription.updated":
            # Subscription updated
            subscription = event.data.object
            StripeService.update_subscription_status(
                db,
                subscription.id,
                subscription.status,
                subscription.cancel_at_period_end
            )
            logger.info(f"Updated subscription {subscription.id}")
        
        elif event_type == "customer.subscription.deleted":
            # Subscription canceled
            subscription = event.data.object
            StripeService.update_subscription_status(
                db,
                subscription.id,
                "canceled"
            )
            logger.info(f"Canceled subscription {subscription.id}")
        
        elif event_type == "invoice.payment_failed":
            # Payment failed
            invoice = event.data.object
            subscription_id = invoice.subscription
            StripeService.update_subscription_status(
                db,
                subscription_id,
                "past_due"
            )
            logger.warning(f"Payment failed for subscription {subscription_id}")
        
        elif event_type == "invoice.payment_succeeded":
            # Payment succeeded
            invoice = event.data.object
            subscription_id = invoice.subscription
            if subscription_id:
                StripeService.update_subscription_status(
                    db,
                    subscription_id,
                    "active"
                )
                logger.info(f"Payment succeeded for subscription {subscription_id}")
        
        return {"status": "success", "event_type": event_type}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )
