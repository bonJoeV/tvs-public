# Gmail to Momence - Automated Email Forwarder

![Version](https://img.shields.io/badge/version-1.1-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A Google Apps Script designed to automatically forward emails from new leads (senders not in your Google Contacts) to your Momence inbox. This script is the automation tool that enables Momence's **'Enable incoming emails propagation'** feature.

---

## ⭐ Purpose & Context

Momence can now create new lead profiles and log all client conversations automatically when you forward emails to your unique Momence address. This script automates that process.

By using this script, you achieve a **single source of truth for all client communication**. When an email arrives from a new person, this script forwards it, Momence creates a new lead, and the message is logged on their profile. All future replies are also captured, building a complete communication history directly within Momence.

* **[Read the official Momence article for more context](https://intercom.help/momence/en/articles/11786746-inbox-update-email-forwarding-is-now-live)**

This script intelligently filters out mailing lists and allows for custom denylists, ensuring only relevant emails from potential new clients are forwarded. It then archives the conversation to keep your main inbox clean.

---

## 🚀 Features

* **Automated Forwarding:** Runs automatically every 10 minutes to process new emails.
* **Contact Detection:** Only forwards emails from senders who are NOT in your Google Contacts.
* **Mailing List Filtering:** Intelligently detects and ignores newsletters and promotional emails.
* **Custom Denylists:** Easily specify email addresses or entire domains to ignore.
* **Auto-Archive:** Cleans your inbox by automatically archiving threads after forwarding.
* **Safe Mode:** Includes a `TEST_MODE` to log actions without forwarding or archiving, allowing you to verify its behavior safely.
* **Simple Setup:** A one-click `automatedSetup` function creates the necessary Gmail label and the 10-minute trigger for you.

---

## 🛠️ Setup Instructions

Follow these steps to get the script running in your Google Account.

> **Important Prerequisite:** Before you begin, please ensure you are logged into the correct Google account for your TVS Studio. All steps must be performed within that specific account.

### Step 1: Create the Apps Script Project

1.  Go to [script.google.com](https://script.google.com) and click **New project**.
2.  Give the project a name (e.g., "Momence Email Forwarder").
3.  You will see two files in the editor sidebar: `Code.gs` and `appsscript.json`. If you don't see `appsscript.json`, go to **Project Settings** ⚙️ and check the box **Show "appsscript.json" manifest file in editor**.

### Step 2: Add the Code

1.  Copy the entire contents of the `Code.gs` file from this repository.
2.  Paste it into the `Code.gs` file in your Apps Script project, replacing all existing code.
3.  Copy the entire contents of the `appsscript.json` file from this repository.
4.  Paste it into the `appsscript.json` file in your project, replacing its contents.

### Step 3: Configure the Script

1.  In the `Code.gs` file, find the **CONFIGURATION** section at the top.
2.  Change the `FORWARD_TO` variable to your unique Momence email address (e.g., `your-name@in.momence.com`).
3.  Review the `DENY_LIST_EMAILS` and `DENY_LIST_DOMAINS` and add any others you wish to ignore.
4.  Leave `TEST_MODE` as `true` for now.
5.  Save the project by clicking the floppy disk icon or pressing `Ctrl+S`.

### Step 4: Run the One-Time Automated Setup

1.  At the top of the editor, ensure the function dropdown menu says `automatedSetup`.
2.  Click the **Run** button.
3.  A pop-up will appear asking for authorization. Review the permissions and grant them.
4.  **Important:** The first time you run this, you may see an error in the logs that the People API needs to be enabled. This error message will include a direct link to the Google Cloud Console. Click that link, press the **Enable** button, and then **Run** the `automatedSetup` function one more time.
5.  Check the "Execution log" at the bottom of the screen. You should see a message: "✅ Setup is complete."

### Step 5: Go Live

The script is now running automatically every 10 minutes in test mode. It will log which emails it *would* forward. Once you have checked the logs and are happy with its behavior:

1.  Change the `TEST_MODE` variable in the `Code.gs` configuration from `true` to `false`.
2.  Save the project.

The script is now live and will actively forward and archive new lead emails.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.