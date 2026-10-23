# Tidepool Tea Store (Flask + Stripe)

## Overview

A complete small eCommerce store built with Flask and Stripe payments.

## Description

The store includes a product catalogue, a session-based shopping cart, user registration and login, and order history stored in a database.  
Payments are handled by Stripe Checkout in test mode, with secure password hashing, CSRF protection, and an optional webhook to confirm orders.

### Test Payment

This project runs in Stripe test mode, so no real money is charged. On the Stripe payment page, use:

- **Card number:** `4242 4242 4242 4242`
- **Expiry date:** Any future date (e.g., `12/30`)
- **CVC:** Any three-digit number (e.g., `123`)

## Demo

![Store Demo](demo.gif)
