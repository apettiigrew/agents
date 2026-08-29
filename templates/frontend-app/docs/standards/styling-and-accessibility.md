# Styling & Accessibility

Tailwind for styling, semantic HTML for structure, keyboard and screen reader for every interaction. Accessibility isn't a pass at the end; it's how the markup is written.

## Styling

- **Tailwind utilities in JSX.** No CSS Modules, no styled-components/Emotion, no `@apply` except in `globals.css` for base element styles.
- Design tokens live in `tailwind.config.ts` (`theme.extend`): colors, spacing, radii, fonts, shadows. Never hard-code hex values or pixel magic numbers in class strings — `bg-brand-600`, not `bg-[#1f4fd8]`. Arbitrary values (`w-[137px]`) need a comment explaining why.
- Variants with `class-variance-authority`:
  ```ts
  const button = cva('inline-flex items-center rounded-md font-medium transition focus-visible:ring-2', {
    variants: {
      intent: { primary: 'bg-brand-600 text-white hover:bg-brand-700', ghost: 'hover:bg-neutral-100' },
      size: { sm: 'h-8 px-3 text-sm', md: 'h-10 px-4' },
    },
    defaultVariants: { intent: 'primary', size: 'md' },
  });
  ```
- Merge classes with `cn()` (`clsx` + `tailwind-merge`). Components accept `className` and apply it last.
- Class order is enforced by `prettier-plugin-tailwindcss`. Don't fight it.
- Dark mode via `class` strategy and `dark:` variants using tokens; never a second set of components.
- Inline `style` only for values computed at runtime (`style={{ width: \`${pct}%\` }}`).
- Responsive: mobile-first. Base classes are the small screen; `md:`/`lg:` add up. Test at 360px, 768px, 1280px.
- Motion respects `motion-reduce:`; no animation longer than 300ms for UI feedback.

## Design system primitives (`components/ui/`)

- Built on **Radix UI** primitives (or the repo's chosen headless library) for anything with keyboard/focus semantics: Dialog, Popover, Select, Tabs, Tooltip, Dropdown. Never hand-roll these — the a11y is the hard part.
- Each primitive: `className` passthrough, `ref` forwarding, `cva` variants, a Storybook story (if Storybook is in the repo), and a test of the keyboard contract.
- Icons from one library (`lucide-react`), sized with Tailwind, `aria-hidden` when decorative, `aria-label` on the button (not the icon) when they're the only content.

## Semantic HTML

- Landmarks: one `<main>`, `<nav aria-label>`, `<header>`, `<footer>`, `<aside>`. Headings form an outline (`h1` once per page, no skipped levels — CSS handles the size, not the tag choice).
- Buttons do things; links go places. `<button type="button">` for actions, `<Link>` for navigation. Never `<div onClick>`; never `<a href="#">`.
- Lists are `<ul>/<ol>`; tables are `<table>` with `<th scope>`; forms are `<form>` with a submit button.
- `<button>` inside a `<form>` defaults to `type="submit"` — set `type="button"` explicitly for non-submit buttons.

## Forms & controls

- Every control has a visible `<label htmlFor>`. Placeholder is not a label. Visually-hidden labels (`sr-only`) only for search boxes with an obvious icon.
- Errors: `aria-invalid="true"` on the control, message linked via `aria-describedby`, announced with `role="alert"` on submit.
- Required fields marked with `required` + visible indicator; explain the indicator once at the top of the form.
- Group related controls in `<fieldset><legend>`.
- Autocomplete attributes on personal-data fields (`autoComplete="email"`, `"postal-code"`, …).

## Keyboard & focus

- Everything clickable is reachable with Tab and operable with Enter/Space. Custom widgets follow the WAI-ARIA Authoring Practices pattern for their role (arrow keys in menus/tabs, Escape closes overlays).
- Visible focus ring on every interactive element: `focus-visible:ring-2 focus-visible:ring-offset-2`. Never `outline-none` without a replacement.
- Focus management: opening a dialog moves focus in and traps it; closing returns focus to the trigger (Radix does this). After a route change, focus the `h1` or `main`. After deleting an item, focus the next item or the list heading.
- No positive `tabIndex`. `tabIndex={-1}` only for programmatic focus targets.
- Skip link as the first focusable element in the root layout.

## Screen readers & ARIA

- First rule of ARIA: don't, if a native element does it. `<button>` over `<div role="button">`.
- Live regions for async feedback: toasts in `role="status"` (polite), errors in `role="alert"`. One persistent live region in the layout beats many transient ones.
- Loading: `aria-busy="true"` on the region, skeleton marked `aria-hidden`, and a visually-hidden "Loading orders…" for screen readers.
- Icon-only buttons have `aria-label`. Decorative images have `alt=""`; informative images describe the content, not "image of".
- Don't announce everything. `aria-live` on a list that re-renders on every keystroke is worse than nothing.

## Color & content

- Contrast ≥ 4.5:1 for text, ≥ 3:1 for large text and UI boundaries. Tokens in the Tailwind config are pre-checked; adding a token means checking it.
- Never convey state by color alone: status badges have text or an icon; error inputs have a message, not just a red border.
- Text resizes to 200% without loss; layouts use `rem`, not `px`, for type and spacing.
- Language: `<html lang>` set; `lang` attribute on foreign-language fragments.

## Tooling gates

- `eslint-plugin-jsx-a11y` (recommended + `strict` rules for labels/roles) — errors, not warnings.
- `@axe-core/playwright` runs on every page in the E2E suite: `expect(await new AxeBuilder({ page }).analyze()).toHaveNoViolations()` — critical/serious violations fail CI.
- Manual check before marking a UI task done: Tab through the whole flow once; run it once with VoiceOver/NVDA if you built a new widget.

## Anti-patterns (reject in review)

- `<div onClick>`, `<span role="button">`, `outline-none` without replacement.
- Hex colors or arbitrary pixel values in class strings.
- Placeholder-as-label; unlabelled icon buttons.
- Hand-rolled dropdown/modal/tooltip.
- Status shown by color only.
- `aria-label` overriding visible text with different wording (breaks voice control).
