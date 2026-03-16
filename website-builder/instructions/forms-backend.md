# Forms & Backend

Contact forms, newsletter signups, and server actions.

---

## Contact Form with Server Action

### Option 1: Email via Resend (recommended)

```bash
pnpm add resend
```

Add to `.env.local`:
```
RESEND_API_KEY=re_xxxxx
CONTACT_EMAIL=hello@example.com
```

Create the server action:

```tsx
// src/app/actions/contact.ts
"use server";

import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

interface ContactFormData {
  name: string;
  email: string;
  phone?: string;
  message: string;
}

export async function submitContactForm(data: ContactFormData) {
  // Validate
  if (!data.name || !data.email || !data.message) {
    return { success: false, error: "Please fill in all required fields." };
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    return { success: false, error: "Please enter a valid email address." };
  }

  try {
    await resend.emails.send({
      from: "Website Contact <noreply@yourdomain.com>",
      to: process.env.CONTACT_EMAIL!,
      replyTo: data.email,
      subject: `New contact from ${data.name}`,
      html: `
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> ${data.name}</p>
        <p><strong>Email:</strong> ${data.email}</p>
        ${data.phone ? `<p><strong>Phone:</strong> ${data.phone}</p>` : ""}
        <hr />
        <p><strong>Message:</strong></p>
        <p>${data.message.replace(/\n/g, "<br />")}</p>
      `,
    });

    return { success: true };
  } catch (error) {
    console.error("Contact form error:", error);
    return { success: false, error: "Something went wrong. Please try again." };
  }
}
```

### Update ContactForm.tsx to use server action:

```tsx
// In the handleSubmit function, replace the TODO with:
import { submitContactForm } from "@/app/actions/contact";

async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
  e.preventDefault();
  setIsSubmitting(true);
  setError("");

  const formData = new FormData(e.currentTarget);
  const result = await submitContactForm({
    name: formData.get("name") as string,
    email: formData.get("email") as string,
    phone: formData.get("phone") as string,
    message: formData.get("message") as string,
  });

  setIsSubmitting(false);

  if (result.success) {
    setIsSubmitted(true);
  } else {
    setError(result.error || "Something went wrong.");
  }
}
```

---

### Option 2: AgentMail (if available in platform keys)

Use the AgentMail API for form submissions:

```tsx
// src/app/actions/contact.ts
"use server";

export async function submitContactForm(data: ContactFormData) {
  if (!data.name || !data.email || !data.message) {
    return { success: false, error: "Please fill in all required fields." };
  }

  try {
    const response = await fetch("https://api.agentmail.to/v0/inboxes/YOUR_INBOX_ID/messages", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.AGENTMAIL_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: { email: data.email, name: data.name },
        subject: `Contact form: ${data.name}`,
        body_text: `Name: ${data.name}\nEmail: ${data.email}\nPhone: ${data.phone || "N/A"}\n\n${data.message}`,
      }),
    });

    if (!response.ok) throw new Error("AgentMail API error");
    return { success: true };
  } catch (error) {
    console.error("Contact form error:", error);
    return { success: false, error: "Something went wrong. Please try again." };
  }
}
```

---

### Option 3: No Email Service (file-based fallback)

If no email API is available, save submissions to a JSON file on the server:

```tsx
// src/app/actions/contact.ts
"use server";

import fs from "fs";
import path from "path";

export async function submitContactForm(data: ContactFormData) {
  if (!data.name || !data.email || !data.message) {
    return { success: false, error: "Please fill in all required fields." };
  }

  try {
    const submissionsPath = path.join(process.cwd(), "data", "contact-submissions.json");

    // Ensure directory exists
    const dir = path.dirname(submissionsPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    // Read existing submissions
    let submissions = [];
    if (fs.existsSync(submissionsPath)) {
      submissions = JSON.parse(fs.readFileSync(submissionsPath, "utf8"));
    }

    // Add new submission
    submissions.push({
      ...data,
      submittedAt: new Date().toISOString(),
      id: Date.now().toString(),
    });

    // Write back
    fs.writeFileSync(submissionsPath, JSON.stringify(submissions, null, 2));

    return { success: true };
  } catch (error) {
    console.error("Contact form error:", error);
    return { success: false, error: "Something went wrong. Please try again." };
  }
}
```

This saves to `data/contact-submissions.json` in the project. The agent or admin can check submissions via the file.

---

## Newsletter Signup

Simple email collection component:

```tsx
"use client";
import { useState } from "react";
import { ArrowRight, CheckCircle } from "lucide-react";

export function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");

    // TODO: Replace with your email service (Resend audience, Mailchimp, etc.)
    // For now, save to file like contact form fallback
    try {
      const res = await fetch("/api/newsletter", {
        method: "POST",
        body: JSON.stringify({ email }),
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        setStatus("success");
        setEmail("");
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <div className="flex items-center gap-2 text-sm text-primary">
        <CheckCircle className="w-4 h-4" />
        Thanks for subscribing!
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email"
        required
        className="flex-grow px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
      />
      <button
        type="submit"
        disabled={status === "loading"}
        className="px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors cursor-pointer disabled:opacity-50"
      >
        {status === "loading" ? "..." : <ArrowRight className="w-4 h-4" />}
      </button>
    </form>
  );
}
```

Add to Footer:
```tsx
import { NewsletterSignup } from "@/components/shared/NewsletterSignup";

// In the Footer brand column:
<div className="mt-6">
  <p className="text-sm font-medium mb-2">Stay Updated</p>
  <NewsletterSignup />
</div>
```

---

## API Routes (alternative to server actions)

If you prefer API routes over server actions:

```tsx
// src/app/api/contact/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const data = await req.json();

  // Validate and process...

  return NextResponse.json({ success: true });
}
```

Call from client:
```tsx
const res = await fetch("/api/contact", {
  method: "POST",
  body: JSON.stringify(formData),
  headers: { "Content-Type": "application/json" },
});
```
