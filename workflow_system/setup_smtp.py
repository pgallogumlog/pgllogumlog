"""
SMTP Setup Helper.

This script helps you set up SMTP email sending with Gmail.
"""

import os
import sys


def main():
    print("=" * 70)
    print("SMTP Email Setup for Gmail")
    print("=" * 70)

    env_file = ".env"

    if not os.path.exists(env_file):
        print(f"\nERROR: {env_file} not found!")
        print("Please create it from .env.example first:")
        print("  cp .env.example .env")
        return

    print("\nTo send emails via Gmail, you need an App Password.")
    print("\nSteps to get Gmail App Password:")
    print("  1. Go to: https://myaccount.google.com/security")
    print("  2. Enable 2-Factor Authentication if not already enabled")
    print("  3. Go to: https://myaccount.google.com/apppasswords")
    print("  4. Select 'Mail' and your device")
    print("  5. Click 'Generate'")
    print("  6. Copy the 16-character password")

    print("\n" + "=" * 70)
    print("Add these lines to your .env file:")
    print("=" * 70)

    email = input("\nEnter your Gmail address: ").strip()
    if not email:
        email = "your-email@gmail.com"

    print(f"\n# SMTP Email Settings (for sending emails)")
    print(f"SMTP_HOST=smtp.gmail.com")
    print(f"SMTP_PORT=587")
    print(f"SMTP_USER={email}")
    print(f"SMTP_PASSWORD=your-16-char-app-password-here")
    print(f"SMTP_FROM_EMAIL={email}")
    print(f"SMTP_USE_TLS=true")

    print("\n" + "=" * 70)
    print("\nAfter adding these to .env, test with:")
    print("  python run_test.py --send-emails --tier standard --count 1")
    print("=" * 70)


if __name__ == "__main__":
    main()
