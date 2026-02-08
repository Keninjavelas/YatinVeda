// Global Razorpay type declaration

declare global {
  interface Window {
    Razorpay: new (options: RazorpayOptions) => { open: () => void };
  }
  interface RazorpayOptions {
    key: string;
    amount: number;
    currency: string;
    name: string;
    description: string;
    order_id: string;
    handler: (response: unknown) => void;
    prefill: { name: string; email: string; contact: string };
    theme: { color: string };
  }
}

export {};