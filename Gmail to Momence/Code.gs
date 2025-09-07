/**
 * ===================================================================================
 * Script:      Forward Non-Contact Emails to Momence
 * Author:      Joe Vandermark (Joe@thevitalstretch.com)
 * Date:        07Sep2025
 * Version:     1.2 (Bug Fix)
 *
 * PURPOSE:
 * This script automates forwarding emails from new leads to the Momence platform.
 * See the instructions above for the simplified setup process using the manifest file.
 *
 * v1.2 Changes:
 * - Fixed TypeError: thread.removeFromInbox() is not a function. Replaced with thread.moveToArchive().
 * - Fixed TypeError where thread.hasLabel() was used. Replaced with a helper function.
 * ===================================================================================
 */

// --- START CONFIGURATION ---

const FORWARD_TO = "49534-l5ma0@forwarding.momence.com"; // IMPORTANT: Change this to your Momence email
const FORWARDED_LABEL = "forwarded_non_contact";
const MAX_THREADS_PER_RUN = 50;
const LOOKBACK_MINUTES = 10;
const TEST_MODE = false;                                  // true = log only, false = actually forward and archive

/**
 * DENYLIST: Add specific email addresses or entire domains here to prevent them
 * from being forwarded. All entries should be lowercase.
 */
const DENY_LIST_EMAILS = [
  'security@mail.instagram.com',
  'eric@sellingwellnessstrategies.com',
  'email@aroma360.com',
  'calendar-notification@google.com',
  'drive-noreply@google.com',
  'webmaster@google.com',
  'google-noreply@google.com',
  'voice-noreply@google.com',
  'accounts.google.com'
];

const DENY_LIST_DOMAINS = [
  'mail.momence.com',
  'social-fitness.com',
  'mg2.social-fitness.co',
  'dbaplatform.com',
  'thevitalstretch.com',
  'kinotek.com'
];

// --- END CONFIGURATION ---


/**
 * Run this function ONCE to automatically create the label and the 10-minute trigger.
 */
function automatedSetup() {
  Logger.log("Starting automated setup...");
  try {
    // 1. Create the Gmail label
    getOrCreateLabel_(FORWARDED_LABEL);
    Logger.log(`Label "${FORWARDED_LABEL}" is ready.`);

    // 2. Delete any old triggers to prevent duplicates
    const existingTriggers = ScriptApp.getProjectTriggers();
    existingTriggers.forEach(trigger => {
      if (trigger.getHandlerFunction() === "processInbox") {
        ScriptApp.deleteTrigger(trigger);
        Logger.log("Removed an old trigger to prevent duplication.");
      }
    });

    // 3. Create the new time-driven trigger
    ScriptApp.newTrigger("processInbox")
      .timeBased()
      .everyMinutes(5)
      .create();
    Logger.log("Successfully created a new trigger to run 'processInbox' every 5 minutes.");
    Logger.log("✅ Setup is complete. You can 'Go Live' by setting TEST_MODE to false.");
  } catch(e) {
    Logger.log(`ERROR during setup: ${e.message}`);
    Logger.log("This may be because the People API is not enabled in the Cloud Console project. If you saw a link to enable it, please click it, then run this setup again.");
  }
}


/**
 * This is the main function that the trigger will run automatically.
 */
function processInbox() {
  if (FORWARD_TO.includes("your-unique-address") || FORWARD_TO.includes("you@example.com")) {
    Logger.log("HALTING: The 'FORWARD_TO' variable has not been set. Please update the script configuration.");
    return;
  }

  const contactSet = buildContactEmailSet_();
  if (!contactSet) {
    Logger.log("HALTING: Could not build the contact list. Aborting run to prevent forwarding all emails.");
    return;
  }

  const query = `in:inbox newer_than:${LOOKBACK_MINUTES}m -label:${FORWARDED_LABEL}`;
  const threads = GmailApp.search(query, 0, MAX_THREADS_PER_RUN);
  if (!threads.length) {
    if (TEST_MODE) Logger.log("No new, unprocessed threads found.");
    return;
  }

  threads.forEach(thread => {
    if (threadHasLabel_(thread, FORWARDED_LABEL)) return;

    const msgs = thread.getMessages();
    for (const msg of msgs) {
      if (msg.isInTrash() || msg.isDraft() || threadHasLabel_(thread, FORWARDED_LABEL)) continue;

      if (isMailingList_(msg)) {
        if (TEST_MODE) Logger.log(`Skipping mailing list: "${msg.getSubject()}"`);
        thread.addLabel(getOrCreateLabel_(FORWARDED_LABEL));
        continue;
      }

      const senderEmail = extractEmail_(msg.getFrom() || "");
      if (!senderEmail) continue;

      const senderEmailLower = senderEmail.toLowerCase();
      const senderDomain = senderEmailLower.substring(senderEmailLower.indexOf('@') + 1);

      const isKnown = contactSet.has(senderEmailLower) ||
                      DENY_LIST_EMAILS.includes(senderEmailLower) ||
                      DENY_LIST_DOMAINS.includes(senderDomain);

      if (!isKnown) {
        let wasForwarded = false;
        if (TEST_MODE) {
          Logger.log(`TEST MODE: Would forward and archive email from non-contact ${senderEmail}: "${msg.getSubject()}"`);
          wasForwarded = true;
        } else {
          try {
            msg.forward(FORWARD_TO);
            Logger.log(`Successfully forwarded and archived email from ${senderEmail} to Momence.`);
            wasForwarded = true;
          } catch (e) {
            Logger.log(`ERROR: Forward failed for ${senderEmail}: ${e}`);
          }
        }
        if (wasForwarded) {
          thread.addLabel(getOrCreateLabel_(FORWARDED_LABEL));
          thread.moveToArchive(); // CORRECTED LINE
        }
      }
    }
  });
}

/* ================== Helper Functions ================== */

/**
 * Correctly checks if a GmailThread has a specific label by name.
 * @param {GmailApp.GmailThread} thread The thread to check.
 * @param {string} labelName The name of the label.
 * @returns {boolean} True if the label exists on the thread.
 */
function threadHasLabel_(thread, labelName) {
  const labels = thread.getLabels();
  for (let i = 0; i < labels.length; i++) {
    if (labels[i].getName() === labelName) {
      return true;
    }
  }
  return false;
}

function buildContactEmailSet_() {
  const set = new Set();
  set.add(Session.getActiveUser().getEmail().toLowerCase());
  let pageToken = null;
  try {
    const res = People.People.Connections.list("people/me", {
      personFields: "emailAddresses",
      pageSize: 1000,
      pageToken
    });
    const conns = res.connections || [];
    conns.forEach(p => {
      (p.emailAddresses || []).forEach(e => {
        const v = (e.value || "").trim().toLowerCase();
        if (v) set.add(v);
      });
    });
    return set;
  } catch (e) {
    Logger.log(`CRITICAL ERROR fetching contacts: ${e.message}. Please ensure the People API is enabled.`);
    return null;
  }
}

function getOrCreateLabel_(name) {
  return GmailApp.getUserLabelByName(name) || GmailApp.createLabel(name);
}

function extractEmail_(fromHeader) {
  const match = fromHeader.match(/<([^>]+)>/);
  if (match && match[1]) return match[1].trim();
  const simple = fromHeader.trim();
  if (simple.includes("@")) return simple;
  return null;
}

function isMailingList_(msg) {
  try {
    if (msg.getHeader("List-Id") || msg.getHeader("List-Unsubscribe")) return true;
    const precedence = msg.getHeader("Precedence");
    if (precedence && /list|bulk|junk/i.test(precedence)) return true;
    const xList = msg.getHeader("X-Mailing-List") || msg.getHeader("X-List");
    if (xList) return true;
  } catch (e) { /* Failsafe */ }
  return false;
}