/** Asklevia Tailwind preset. Import tokens.css once, then: presets: [require('./tailwind.preset.js')] */
module.exports = {
  "theme": {
    "extend": {
      "colors": {
        "neutral-0": "var(--neutral-0)",
        "neutral-25": "var(--neutral-25)",
        "neutral-50": "var(--neutral-50)",
        "neutral-100": "var(--neutral-100)",
        "neutral-200": "var(--neutral-200)",
        "neutral-300": "var(--neutral-300)",
        "neutral-400": "var(--neutral-400)",
        "neutral-500": "var(--neutral-500)",
        "neutral-600": "var(--neutral-600)",
        "neutral-700": "var(--neutral-700)",
        "neutral-800": "var(--neutral-800)",
        "neutral-900": "var(--neutral-900)",
        "indigo-50": "var(--indigo-50)",
        "indigo-100": "var(--indigo-100)",
        "indigo-200": "var(--indigo-200)",
        "indigo-300": "var(--indigo-300)",
        "indigo-500": "var(--indigo-500)",
        "indigo-600": "var(--indigo-600)",
        "indigo-700": "var(--indigo-700)",
        "spectrum-violet": "var(--spectrum-violet)",
        "spectrum-azure": "var(--spectrum-azure)",
        "spectrum-teal": "var(--spectrum-teal)",
        "spectrum-verdant": "var(--spectrum-verdant)",
        "spectrum-violet-50": "var(--spectrum-violet-50)",
        "spectrum-azure-50": "var(--spectrum-azure-50)",
        "spectrum-teal-50": "var(--spectrum-teal-50)",
        "spectrum-verdant-50": "var(--spectrum-verdant-50)",
        "success-600": "var(--success-600)",
        "success-50": "var(--success-50)",
        "warning-600": "var(--warning-600)",
        "warning-50": "var(--warning-50)",
        "danger-600": "var(--danger-600)",
        "danger-700": "var(--danger-700)",
        "danger-50": "var(--danger-50)",
        "info-600": "var(--info-600)",
        "info-50": "var(--info-50)",
        "bg-page": "var(--bg-page)",
        "bg-surface": "var(--bg-surface)",
        "bg-subtle": "var(--bg-subtle)",
        "bg-brand-subtle": "var(--bg-brand-subtle)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-tertiary": "var(--text-tertiary)",
        "text-disabled": "var(--text-disabled)",
        "text-brand": "var(--text-brand)",
        "text-on-brand": "var(--text-on-brand)",
        "border-default": "var(--border-default)",
        "border-strong": "var(--border-strong)",
        "border-control": "var(--border-control)",
        "action-primary": "var(--action-primary)",
        "action-primary-hover": "var(--action-primary-hover)",
        "action-primary-active": "var(--action-primary-active)",
        "focus-ring": "var(--focus-ring)"
      },
      "fontFamily": {
        "display": [
          "var(--font-display)"
        ],
        "sans": [
          "var(--font-sans)"
        ],
        "mono": [
          "var(--font-mono)"
        ]
      },
      "fontSize": {
        "display-xl": [
          "56px",
          {
            "lineHeight": "60px",
            "fontWeight": "500",
            "letterSpacing": "-0.02em"
          }
        ],
        "display-lg": [
          "44px",
          {
            "lineHeight": "48px",
            "fontWeight": "500",
            "letterSpacing": "-0.02em"
          }
        ],
        "heading-1": [
          "34px",
          {
            "lineHeight": "40px",
            "fontWeight": "500",
            "letterSpacing": "-0.015em"
          }
        ],
        "heading-2": [
          "26px",
          {
            "lineHeight": "32px",
            "fontWeight": "500",
            "letterSpacing": "-0.01em"
          }
        ],
        "heading-3": [
          "20px",
          {
            "lineHeight": "28px",
            "fontWeight": "500",
            "letterSpacing": "-0.005em"
          }
        ],
        "body-lg": [
          "18px",
          {
            "lineHeight": "28px",
            "fontWeight": "400",
            "letterSpacing": "0em"
          }
        ],
        "body": [
          "16px",
          {
            "lineHeight": "24px",
            "fontWeight": "400",
            "letterSpacing": "0em"
          }
        ],
        "body-sm": [
          "14px",
          {
            "lineHeight": "20px",
            "fontWeight": "400",
            "letterSpacing": "0em"
          }
        ],
        "label": [
          "14px",
          {
            "lineHeight": "20px",
            "fontWeight": "600",
            "letterSpacing": "0em"
          }
        ],
        "caption": [
          "12px",
          {
            "lineHeight": "16px",
            "fontWeight": "500",
            "letterSpacing": "0.01em"
          }
        ],
        "overline": [
          "12px",
          {
            "lineHeight": "16px",
            "fontWeight": "600",
            "letterSpacing": "0.06em"
          }
        ],
        "mono": [
          "13px",
          {
            "lineHeight": "20px",
            "fontWeight": "400",
            "letterSpacing": "0em"
          }
        ],
        "mono-lg": [
          "16px",
          {
            "lineHeight": "24px",
            "fontWeight": "500",
            "letterSpacing": "0em"
          }
        ]
      },
      "spacing": {
        "0": "0px",
        "0.5": "2px",
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px",
        "24": "96px"
      },
      "borderRadius": {
        "xs": "4px",
        "sm": "8px",
        "md": "12px",
        "lg": "16px",
        "xl": "24px",
        "pill": "999px"
      },
      "boxShadow": {
        "xs": "0 1px 2px rgba(15,18,34,0.06)",
        "sm": "0 1px 2px rgba(15,18,34,0.06), 0 2px 6px rgba(15,18,34,0.06)",
        "md": "0 8px 24px rgba(15,18,34,0.10), 0 2px 6px rgba(15,18,34,0.06)",
        "lg": "0 24px 56px rgba(43,47,217,0.14), 0 4px 12px rgba(15,18,34,0.08)",
        "focus": "0 0 0 2px #FFFFFF, 0 0 0 4px #2B2FD9"
      },
      "zIndex": {
        "dropdown": "1000",
        "sticky": "1100",
        "overlay": "1200",
        "modal": "1300",
        "toast": "1400",
        "tooltip": "1500"
      },
      "transitionDuration": {
        "fast": "120ms",
        "base": "200ms",
        "slow": "320ms"
      },
      "transitionTimingFunction": {
        "standard": "cubic-bezier(0.2, 0.8, 0.2, 1)",
        "exit": "cubic-bezier(0.4, 0, 1, 1)"
      },
      "screens": {
        "sm": "640px",
        "md": "768px",
        "lg": "1024px",
        "xl": "1280px"
      },
      "backgroundImage": {
        "spectrum": "var(--spectrum-gradient)"
      },
      "maxWidth": {
        "content": "1200px"
      }
    }
  }
};
