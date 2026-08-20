import tkinter as tk
from tkinter import ttk
import urllib.request
import json
import threading

URL = "http://localhost:8000/webhook"

webhooks = {
    "1": {
        "name": "payment.failed",
        "payload": {
            "account_id": "acc_test_123",
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_xyz123",
                        "email": "angry.customer@example.com",
                        "contact": "9876543210",
                        "card_number": "4111111111111111",
                        "error_description": "insufficient_funds"
                    }
                }
            }
        }
    },
    "2": {
        "name": "payment.dispute.created",
        "payload": {
            "account_id": "acc_test_123",
            "event": "payment.dispute.created",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_dispute_001",
                        "email": "customer@example.com",
                        "contact": "9876543210",
                        "amount": 49900,
                        "currency": "INR",
                        "dispute_id": "disp_test_001",
                        "dispute_reason": "fraud"
                    }
                }
            }
        }
    },
    "3": {
        "name": "subscription.halted",
        "payload": {
            "account_id": "acc_test_123",
            "event": "subscription.halted",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_test_halted_001",
                        "customer_id": "cust_test_001",
                        "email": "customer@example.com",
                        "plan_id": "plan_test_monthly",
                        "status": "halted",
                        "reason": "payment_failure",
                        "halted_at": 1724169600
                    }
                }
            }
        }
    }
}

class WebhookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Webhook Trigger Dashboard")
        self.root.geometry("600x500")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Header Frame
        header_frame = tk.Frame(root, bg="#1e1e2e")
        header_frame.pack(fill=tk.X, pady=20)
        
        title_label = tk.Label(
            header_frame, 
            text="Unified Revenue Retention Agent", 
            font=("Segoe UI", 16, "bold"), 
            fg="#cdd6f4", 
            bg="#1e1e2e"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Trigger mock Razorpay webhook events to localhost:8000", 
            font=("Segoe UI", 10), 
            fg="#a6adc8", 
            bg="#1e1e2e"
        )
        subtitle_label.pack(pady=5)

        # Buttons Frame
        btn_frame = tk.Frame(root, bg="#1e1e2e")
        btn_frame.pack(fill=tk.X, padx=50, pady=10)
        
        # Create buttons
        self.create_button(btn_frame, "Trigger payment.failed", "1", "#f38ba8")
        self.create_button(btn_frame, "Trigger payment.dispute.created", "2", "#fab387")
        self.create_button(btn_frame, "Trigger subscription.halted", "3", "#a6e3a1")

        # Logs Frame
        log_frame = tk.Frame(root, bg="#1e1e2e")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        
        log_label = tk.Label(
            log_frame, 
            text="Response Logs", 
            font=("Segoe UI", 11, "bold"), 
            fg="#cdd6f4", 
            bg="#1e1e2e", 
            anchor="w"
        )
        log_label.pack(fill=tk.X, pady=5)
        
        # Logs Text Area
        self.log_text = tk.Text(
            log_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9), 
            bg="#11111b", 
            fg="#89b4fa", 
            insertbackground="#cdd6f4",
            bd=0,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for logs
        scrollbar = ttk.Scrollbar(self.log_text, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_message("System initialized. Ready to trigger webhooks.")

    def create_button(self, parent, text, choice, bg_color):
        btn = tk.Button(
            parent,
            text=text,
            command=lambda: self.trigger_webhook_async(choice),
            font=("Segoe UI", 10, "bold"),
            bg=bg_color,
            fg="#11111b",
            activebackground="#cdd6f4",
            activeforeground="#11111b",
            cursor="hand2",
            bd=0,
            padx=10,
            pady=8,
            relief="flat"
        )
        btn.pack(fill=tk.X, pady=6)
        
        # Hover effects
        def on_enter(e):
            btn.config(bg="#cdd6f4")
        def on_leave(e):
            btn.config(bg=bg_color)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def trigger_webhook_async(self, choice):
        # Run webhook request in a separate thread to prevent GUI freezing
        threading.Thread(target=self.trigger_webhook, args=(choice,), daemon=True).start()

    def trigger_webhook(self, choice):
        webhook = webhooks[choice]
        self.log_message(f"\n[{webhook['name']}] Sending POST request...")
        
        req = urllib.request.Request(
            URL,
            data=json.dumps(webhook['payload']).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as response:
                status = response.status
                body = response.read().decode('utf-8')
                self.log_message(f"[{webhook['name']}] Status Code: {status}")
                self.log_message(f"[{webhook['name']}] Response Body: {body}")
        except urllib.error.HTTPError as e:
            self.log_message(f"[{webhook['name']}] Error: HTTP {e.code}")
            try:
                body = e.read().decode('utf-8')
                self.log_message(f"[{webhook['name']}] Response Body: {body}")
            except:
                pass
        except Exception as e:
            self.log_message(f"[{webhook['name']}] Connection Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebhookGUI(root)
    root.mainloop()
