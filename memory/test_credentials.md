# Test Credentials

## Admin Account (platform owner)
- Email: lzook@plzcompany.com
- Password: HacksterAdmin2025!
- Role: admin
- Use for: Admin panel (/admin), product/vendor management, affiliate analytics, practitioner order queue.

## Demo Member (pre-populated stack for one-click checkout testing)
- Email: demo@hackster.ai
- Password: Demo12345!
- Role: member
- Has a "My Wellness Stack" with 3 items: Thorne Vitamin D-5,000 + Thorne Magnesium (affiliate) and Apex Energetics Resvero Active (practitioner-order). Use to test the "🛒 Buy Stack" one-click grouped checkout.

Note: Both accounts are seeded idempotently on backend startup in initialize_sample_data().
