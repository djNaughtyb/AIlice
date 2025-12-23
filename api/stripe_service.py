"""Stripe payment service for subscription management."""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import stripe
from sqlalchemy.orm import Session

from api.models import Subscription, SubscriptionStatus, User

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe configuration
STRIPE_PRODUCT_ID = os.getenv("STRIPE_PRODUCT_ID", "prod_TYtmG0y2uNXjSU")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_1Sblz7LZxEDQErW5uQyWN5F3")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


class StripeService:
    """Service for handling Stripe payments and subscriptions."""

    @staticmethod
    def create_customer(user: User, email: str) -> str:
        """
        Create a Stripe customer for a user.
        
        Args:
            user: User object
            email: User's email address
            
        Returns:
            Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                metadata={
                    "user_id": user.id,
                    "username": user.username
                }
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        user_id: int,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription.
        
        Args:
            customer_id: Stripe customer ID
            user_id: User ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            metadata: Additional metadata
            
        Returns:
            Checkout session data
        """
        try:
            session_metadata = {
                "user_id": user_id,
            }
            if metadata:
                session_metadata.update(metadata)

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=session_metadata,
                subscription_data={
                    "metadata": session_metadata
                }
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}")
            return {
                "session_id": session.id,
                "url": session.url
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {e}")
            raise

    @staticmethod
    def create_subscription_record(
        db: Session,
        user_id: int,
        stripe_subscription: Any
    ) -> Subscription:
        """
        Create a subscription record in the database.
        
        Args:
            db: Database session
            user_id: User ID
            stripe_subscription: Stripe subscription object
            
        Returns:
            Subscription object
        """
        try:
            # Map Stripe status to our enum
            status_mapping = {
                "active": SubscriptionStatus.ACTIVE,
                "canceled": SubscriptionStatus.CANCELED,
                "past_due": SubscriptionStatus.PAST_DUE,
                "unpaid": SubscriptionStatus.UNPAID,
                "trialing": SubscriptionStatus.TRIALING,
                "incomplete": SubscriptionStatus.INCOMPLETE,
            }
            
            subscription = Subscription(
                user_id=user_id,
                stripe_customer_id=stripe_subscription.customer,
                stripe_subscription_id=stripe_subscription.id,
                stripe_price_id=stripe_subscription.items.data[0].price.id,
                status=status_mapping.get(stripe_subscription.status, SubscriptionStatus.INCOMPLETE),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                cancel_at_period_end=stripe_subscription.cancel_at_period_end
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Created subscription record for user {user_id}")
            return subscription
        except Exception as e:
            logger.error(f"Error creating subscription record: {e}")
            db.rollback()
            raise

    @staticmethod
    def update_subscription_status(
        db: Session,
        stripe_subscription_id: str,
        status: str,
        cancel_at_period_end: bool = False
    ) -> Optional[Subscription]:
        """
        Update subscription status in the database.
        
        Args:
            db: Database session
            stripe_subscription_id: Stripe subscription ID
            status: New status
            cancel_at_period_end: Whether subscription is set to cancel at period end
            
        Returns:
            Updated Subscription object or None
        """
        try:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription {stripe_subscription_id} not found in database")
                return None
            
            # Map Stripe status to our enum
            status_mapping = {
                "active": SubscriptionStatus.ACTIVE,
                "canceled": SubscriptionStatus.CANCELED,
                "past_due": SubscriptionStatus.PAST_DUE,
                "unpaid": SubscriptionStatus.UNPAID,
                "trialing": SubscriptionStatus.TRIALING,
                "incomplete": SubscriptionStatus.INCOMPLETE,
            }
            
            subscription.status = status_mapping.get(status, SubscriptionStatus.INCOMPLETE)
            subscription.cancel_at_period_end = cancel_at_period_end
            subscription.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Updated subscription {stripe_subscription_id} status to {status}")
            return subscription
        except Exception as e:
            logger.error(f"Error updating subscription status: {e}")
            db.rollback()
            raise

    @staticmethod
    def cancel_subscription(
        db: Session,
        stripe_subscription_id: str,
        cancel_immediately: bool = False
    ) -> bool:
        """
        Cancel a subscription.
        
        Args:
            db: Database session
            stripe_subscription_id: Stripe subscription ID
            cancel_immediately: If True, cancel immediately; otherwise cancel at period end
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Cancel in Stripe
            if cancel_immediately:
                stripe.Subscription.delete(stripe_subscription_id)
            else:
                stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Update database
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()
            
            if subscription:
                if cancel_immediately:
                    subscription.status = SubscriptionStatus.CANCELED
                else:
                    subscription.cancel_at_period_end = True
                subscription.updated_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Canceled subscription {stripe_subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Error canceling subscription: {e}")
            return False

    @staticmethod
    def reactivate_subscription(
        db: Session,
        stripe_subscription_id: str
    ) -> bool:
        """
        Reactivate a canceled subscription (before period end).
        
        Args:
            db: Database session
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Reactivate in Stripe
            stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            # Update database
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()
            
            if subscription:
                subscription.cancel_at_period_end = False
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.updated_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Reactivated subscription {stripe_subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Error reactivating subscription: {e}")
            return False

    @staticmethod
    def get_subscription(
        db: Session,
        user_id: int
    ) -> Optional[Subscription]:
        """
        Get active subscription for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Subscription object or None
        """
        return db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
        ).first()

    @staticmethod
    def check_subscription_status(
        db: Session,
        user_id: int
    ) -> bool:
        """
        Check if user has an active subscription.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if user has active subscription, False otherwise
        """
        subscription = StripeService.get_subscription(db, user_id)
        return subscription is not None

    @staticmethod
    def get_invoices(
        customer_id: str,
        limit: int = 10
    ) -> list:
        """
        Get invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoice data
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            
            return [{
                "id": inv.id,
                "amount_due": inv.amount_due,
                "amount_paid": inv.amount_paid,
                "currency": inv.currency,
                "status": inv.status,
                "created": datetime.fromtimestamp(inv.created).isoformat(),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url
            } for inv in invoices.data]
        except stripe.error.StripeError as e:
            logger.error(f"Error getting invoices: {e}")
            return []

    @staticmethod
    def construct_webhook_event(
        payload: bytes,
        sig_header: str
    ) -> Optional[Any]:
        """
        Construct and verify a Stripe webhook event.
        
        Args:
            payload: Request body
            sig_header: Stripe-Signature header
            
        Returns:
            Stripe event object or None
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return None
