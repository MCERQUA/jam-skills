# Social Jam CSS Component Library — Agent Build Menu

> **What this is:** a recipe menu of 119 ready-to-use CSS components (built by Danielle's agent). Build agents READ this to assemble sites — pick components by category, copy the CSS+HTML, apply the selector.

## How to use this menu (agent protocol)

1. **Pick by section, not at random.** Map the page section → category: hero→`text`+`backgrounds`+`buttons`; feature grid→`cards`+`hover`; pricing→`cards`+`borders`(featured)+`buttons`; contact→`forms`+`buttons`; any async→`loaders`.
2. **Copy the component's CSS into a `<style>` block (or your stylesheet) and its HTML into the markup.** Apply the listed `selector`.
3. **Respect the usage note** — most effects say 'one per viewport' or 'verify contrast'. Over-using kills the effect.
4. **One primary style per page.** Don't mix three different glow buttons; choose one CTA treatment and repeat it.
5. **Machine-readable index:** `component-catalog.json` (same components with `selector`/`usage`/`css`/`html` fields) for programmatic selection.

## Composition recipes (combine components → sections)

| Section | Recipe |
|---|---|
| **Hero** | `text` animated headline (1) + `backgrounds` ambient bg + ONE `buttons` CTA. Keep headline contrast 4.5:1 over the bg. |
| **Feature grid** | `cards` container × N in a responsive grid + a `hover` effect on each card. |
| **Pricing** | `cards` for each tier; put a `borders` (animated/glow) on the *featured* tier only; one `buttons` CTA per tier. |
| **Testimonials** | `cards` + subtle `hover`; avoid heavy animation (readability first). |
| **Contact / Quote** | `forms` inputs (labelled) + a `buttons` submit with a `loaders` loading state on submit. |
| **CTA band** | `backgrounds` gradient section + `text` emphasis + one `buttons` CTA. |

## Component catalog by category

### Buttons & CTAs  ·  18 components

_Primary actions, form submits, hero CTAs. One primary style per page; reserve glow/animated variants for the single most important CTA._

**Pairs well with:** hero sections, pricing cards, forms

<details><summary><b>Gradient Button</b> — <code>.fx-btn</code></summary>


*Apply `.fx-btn` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-gradient">Hover Me</button>
```


```css
.fx-btn {
  padding: 10px 28px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  background: linear-gradient(135deg, #3AB54A, #2d9e40, #25a033);
  background-size: 200% 200%;
  animation: gradShift 3s ease infinite;
}
@keyframes gradShift {
  0%,100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

</details>

<details><summary><b>Glow Button</b> — <code>.fx-btn-glow</code></summary>


*Apply `.fx-btn-glow` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-glow">Hover Me</button>
```


```css
.fx-btn-glow {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(58,181,74,0.4), 0 0 30px rgba(58,181,74,0.2);
  transition: box-shadow 0.3s;
}
.fx-btn-glow:hover {
  box-shadow: 0 0 25px rgba(58,181,74,0.4), 0 0 50px rgba(58,181,74,0.3);
}
```

</details>

<details><summary><b>Ripple Button</b> — <code>.fx-btn-ripple</code></summary>


*Apply `.fx-btn-ripple` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-ripple" onclick="addRipple(event,this)">Click Me</button>
```


```css
.fx-btn-ripple {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.4);
  transform: scale(0);
  animation: rippleAnim 0.6s ease-out;
}
@keyframes rippleAnim { to { transform: scale(4); opacity: 0; } }
```

</details>

<details><summary><b>Neon Border Button</b> — <code>.fx-btn-neon</code></summary>


*Apply `.fx-btn-neon` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-neon">Hover Me</button>
```


```css
.fx-btn-neon {
  padding: 10px 28px;
  background: transparent;
  border: 2px solid #3AB54A;
  color: #3AB54A;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(58,181,74,0.4), inset 0 0 10px rgba(58,181,74,0.4);
  transition: all 0.3s;
}
.fx-btn-neon:hover {
  background: rgba(58,181,74,0.15);
  box-shadow: 0 0 20px rgba(58,181,74,0.4), inset 0 0 20px rgba(58,181,74,0.4);
}
```

</details>

<details><summary><b>Slide Fill Button</b> — <code>.fx-btn-slide</code></summary>


*Apply `.fx-btn-slide` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-slide">Hover Me</button>
```


```css
.fx-btn-slide {
  padding: 10px 28px;
  background: transparent;
  border: 2px solid #3AB54A;
  color: #3AB54A;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  z-index: 1;
  overflow: hidden;
}
.fx-btn-slide::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: #3AB54A;
  z-index: -1;
  transition: left 0.3s;
}
.fx-btn-slide:hover { color: #000; }
.fx-btn-slide:hover::before { left: 0; }
```

</details>

<details><summary><b>Pulse Button</b> — <code>.fx-btn-pulse</code></summary>


*Apply `.fx-btn-pulse` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-pulse">Hover Me</button>
```


```css
.fx-btn-pulse {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  animation: btnPulse 2s infinite;
}
@keyframes btnPulse {
  0% { box-shadow: 0 0 0 0 rgba(58,181,74,0.4); }
  70% { box-shadow: 0 0 0 15px rgba(58,181,74,0); }
  100% { box-shadow: 0 0 0 0 rgba(58,181,74,0); }
}
```

</details>

<details><summary><b>Shadow Grow Button</b> — <code>.fx-btn-shadow</code></summary>


*Apply `.fx-btn-shadow` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-shadow">Hover Me</button>
```


```css
.fx-btn-shadow {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}
.fx-btn-shadow:hover {
  box-shadow: 8px 8px 0 rgba(58,181,74,0.5);
  transform: translate(-2px, -2px);
}
```

</details>

<details><summary><b>Outline Rotate Button</b> — <code>.fx-btn-rotate-outline</code></summary>


*Apply `.fx-btn-rotate-outline` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-rotate-outline">Hover Me</button>
```


```css
.fx-btn-rotate-outline {
  padding: 10px 28px;
  font-weight: 600;
  border: 2px solid transparent;
  color: #3AB54A;
  border-radius: 8px;
  cursor: pointer;
  background-image: linear-gradient(#0d1117, #0d1117), linear-gradient(#3AB54A, #2dd4bf);
  background-origin: border-box;
  background-clip: padding-box, border-box;
  transition: all 0.3s;
}
.fx-btn-rotate-outline:hover {
  background-image: linear-gradient(#0d1117, #0d1117), linear-gradient(#f97316, #ec4899);
}
```

</details>

<details><summary><b>Ghost Button</b> — <code>.btn-ghost</code></summary>


*Apply `.btn-ghost` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-ghost">Hover Me</button>
```


```css
.btn-ghost {
  padding: 10px 28px;
  background: transparent;
  border: 2px solid transparent;
  color: #3AB54A;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-ghost:hover {
  border-color: #3AB54A;
  background: rgba(58,181,74,0.1);
}
```

</details>

<details><summary><b>Magnetic Hover Button</b> — <code>.btn-magnetic</code></summary>


*Apply `.btn-magnetic` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-magnetic" onmousemove="magneticBtn(event,this)" onmouseleave="resetMagnetic(this)">Hover Me</button>
```


```css
.btn-magnetic {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s ease-out;
}
/* JS: onmousemove translate btn slightly toward cursor */
```

</details>

<details><summary><b>3D Press Button</b> — <code>.btn-3d</code></summary>


*Apply `.btn-3d` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-3d">Click Me</button>
```


```css
.btn-3d {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transform: translateY(-3px);
  box-shadow: 0 4px 0 rgba(30,140,40,0.8), 0 6px 10px rgba(0,0,0,0.3);
  transition: all 0.1s;
}
.btn-3d:active {
  transform: translateY(0);
  box-shadow: 0 0 0 rgba(30,140,40,0.8), 0 2px 4px rgba(0,0,0,0.2);
}
```

</details>

<details><summary><b>Shimmer Button</b> — <code>.btn-shimmer</code></summary>


*Apply `.btn-shimmer` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-shimmer">Hover Me</button>
```


```css
.btn-shimmer {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.btn-shimmer::after {
  content: '';
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: linear-gradient(to right, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
  transform: rotate(30deg) translateX(-100%);
  animation: shimmer 3s ease-in-out infinite;
}
@keyframes shimmer {
  0% { transform: rotate(30deg) translateX(-100%); }
  100% { transform: rotate(30deg) translateX(100%); }
}
```

</details>

<details><summary><b>Circle Expand Button</b> — <code>.btn-circle-expand</code></summary>


*Apply `.btn-circle-expand` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-circle-expand">Hover Me</button>
```


```css
.btn-circle-expand {
  padding: 10px 28px;
  background: transparent;
  border: 2px solid #3AB54A;
  color: #3AB54A;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  z-index: 1;
}
.btn-circle-expand::before {
  content: '';
  position: absolute;
  width: 0; height: 0;
  background: #3AB54A;
  border-radius: 50%;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.4s, height 0.4s;
  z-index: -1;
}
.btn-circle-expand:hover { color: #000; }
.btn-circle-expand:hover::before { width: 300px; height: 300px; }
```

</details>

<details><summary><b>Skew Hover Button</b> — <code>.btn-skew</code></summary>


*Apply `.btn-skew` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-skew">Hover Me</button>
```


```css
.btn-skew {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.3s;
}
.btn-skew:hover { transform: skewX(-8deg); }
```

</details>

<details><summary><b>Dotted Border Button</b> — <code>.btn-dotted</code></summary>


*Apply `.btn-dotted` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-dotted">Hover Me</button>
```


```css
.btn-dotted {
  padding: 10px 28px;
  background: transparent;
  border: 3px dotted #3AB54A;
  color: #3AB54A;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  z-index: 1;
}
.btn-dotted::before {
  content: '';
  position: absolute;
  inset: 0;
  background: #3AB54A;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s;
  z-index: -1;
}
.btn-dotted:hover { color: #000; }
.btn-dotted:hover::before { transform: scaleX(1); }
```

</details>

<details><summary><b>Pill Morph Button</b> — <code>.btn-pill</code></summary>


*Apply `.btn-pill` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-pill">Hover Me</button>
```


```css
.btn-pill {
  padding: 10px 28px;
  background: #3AB54A;
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.btn-pill:hover {
  border-radius: 50px;
  padding: 10px 40px;
}
```

</details>

<details><summary><b>Morph Button</b> — <code>.btn-morph</code></summary>


*Apply `.btn-morph` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn fx-btn-morph">Hover Me</button>
```


```css
.btn-morph {
  background: #3AB54A;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 28px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.btn-morph:hover {
  border-radius: 50px;
  padding: 14px 40px;
  background: linear-gradient(135deg, #3AB54A, #2dd4bf);
  transform: scale(1.08);
}
```

</details>

<details><summary><b>Icon Button</b> — <code>.btn-icon</code></summary>


*Apply `.btn-icon` to a `<button>`. Use as the page's primary CTA.*


```html
<button class="fx-btn-icon">⚙</button>
```


```css
.btn-icon {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: #161b22;
  border: 2px solid #30363d;
  color: #8b949e;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.btn-icon:hover {
  background: #3AB54A;
  border-color: #3AB54A;
  color: #000;
  transform: rotate(360deg) scale(1.15);
  box-shadow: 0 0 20px rgba(58,181,74,0.4);
}
```

</details>


### Cards & Containers  ·  12 components

_Group related content — feature tiles, pricing, testimonials, product cards. The workhorse of most page sections._

**Pairs well with:** feature grids, pricing tables, testimonial rows

<details><summary><b>Hover Lift Card</b> — <code>.card-lift</code></summary>


*Wrap content in an element with `.card-lift`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-lift"><span class="card-icon">✨</span><span class="card-title-sm">Hover Lift</span></div>
```


```css
.card-lift {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  transition: all 0.3s;
  cursor: pointer;
}
.card-lift:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.4);
  border-color: #3AB54A;
}
```

</details>

<details><summary><b>Glow Border Card</b> — <code>.card-glow</code></summary>


*Wrap content in an element with `.card-glow`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-glow"><span class="card-icon">💡</span><span class="card-title-sm">Glow Border</span></div>
```


```css
.card-glow {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  transition: all 0.3s;
}
.card-glow:hover {
  border-color: #3AB54A;
  box-shadow: 0 0 20px rgba(58,181,74,0.4), 0 0 40px rgba(58,181,74,0.1);
}
```

</details>

<details><summary><b>Tilt Card</b> — <code>.card-tilt</code></summary>


*Wrap content in an element with `.card-tilt`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-tilt" onmousemove="tiltCard(event,this)" onmouseleave="resetTilt(this)"><span class="card-icon">🎯</span><span class="card-title-sm">Tilt Me</span></div>
```


```css
.card-tilt {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  transform-style: preserve-3d;
  transition: transform 0.3s;
  cursor: pointer;
}
/* Add JS: onmousemove rotateX/Y based on mouse position */
```

</details>

<details><summary><b>Flip Card</b> — <code>.flip-container</code></summary>


*Wrap content in an element with `.flip-container`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-flip-container"><div class="fx-card-flip-inner"><div class="fx-card-flip-front">Front</div><div class="fx-card-flip-back">Back</div></div></div>
```


```css
.flip-container { perspective: 400px; }
.flip-inner {
  transition: transform 0.6s;
  transform-style: preserve-3d;
}
.flip-container:hover .flip-inner { transform: rotateY(180deg); }
.flip-front, .flip-back {
  backface-visibility: hidden;
  border-radius: 10px;
}
.flip-back {
  transform: rotateY(180deg);
  background: #3AB54A;
}
```

</details>

<details><summary><b>Gradient Border Card</b> — <code>.card-grad-border</code></summary>


*Wrap content in an element with `.card-grad-border`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-grad-border"><div class="fx-card-grad-border-inner"><span style="font-size:1.3rem">🌈</span><span style="font-size:0.7rem;color:var(--text-dim)">Gradient</span></div></div>
```


```css
.card-grad-border {
  position: relative;
  padding: 2px;
  border-radius: 10px;
}
.card-grad-border::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 10px;
  padding: 2px;
  background: linear-gradient(135deg, #3AB54A, #2dd4bf, #f97316);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}
```

</details>

<details><summary><b>Spotlight Card</b> — <code>.card-spotlight</code></summary>


*Wrap content in an element with `.card-spotlight`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-spotlight" onmousemove="spotlightTrack(event,this)" onmouseleave="spotlightReset(this)"><span class="card-icon">🔦</span><span class="card-title-sm">Spotlight</span></div>
```


```css
.card-spotlight {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}
.card-spotlight::after {
  content: '';
  position: absolute;
  width: 100px; height: 100px;
  background: radial-gradient(circle, rgba(58,181,74,0.25), transparent 70%);
  border-radius: 50%;
  top: var(--mouse-y, 50%);
  left: var(--mouse-x, 50%);
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}
.card-spotlight:hover::after { opacity: 1; }
```

</details>

<details><summary><b>Glassmorphism Card</b> — <code>.card-glass</code></summary>


*Wrap content in an element with `.card-glass`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-glass"><span class="card-icon">🪟</span><span class="card-title-sm" style="color:var(--text-dim)">Glass</span></div>
```


```css
.card-glass {
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  color: #e2e8f0;
}
```

</details>

<details><summary><b>Gradient Overlay Card</b> — <code>.card-grad-overlay</code></summary>


*Wrap content in an element with `.card-grad-overlay`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-grad-overlay" style="z-index:0"><span class="card-icon" style="position:relative;z-index:1">🎨</span><span class="card-title-sm" style="position:relative;z-index:1;color:var(--text-dim)">Overlay</span></div>
```


```css
.card-grad-overlay {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.4s;
  cursor: pointer;
}
.card-grad-overlay::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(58,181,74,0.3), rgba(45,212,191,0.3));
  opacity: 0;
  transition: opacity 0.4s;
  border-radius: 10px;
}
.card-grad-overlay:hover::after { opacity: 1; }
```

</details>

<details><summary><b>Folded Corner Card</b> — <code>.card-folded</code></summary>


*Wrap content in an element with `.card-folded`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-folded"><span class="card-icon">📄</span><span class="card-title-sm">Fold</span></div>
```


```css
.card-folded {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
}
.card-folded::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 0; height: 0;
  border-style: solid;
  border-width: 0 28px 28px 0;
  border-color: transparent #0d1117 transparent transparent;
  filter: drop-shadow(-2px 2px 2px rgba(0,0,0,0.3));
  transition: border-width 0.3s;
}
.card-folded:hover::after { border-width: 0 40px 40px 0; }
```

</details>

<details><summary><b>Shake Card</b> — <code>.card-shake</code></summary>


*Wrap content in an element with `.card-shake`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-shake"><span class="card-icon">📳</span><span class="card-title-sm">Shake Me</span></div>
```


```css
.card-shake {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px;
  cursor: pointer;
  transition: border-color 0.3s;
}
.card-shake:hover {
  border-color: #f97316;
  animation: cardShake 0.5s ease;
}
@keyframes cardShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}
```

</details>

<details><summary><b>Conic Gradient Card</b> — <code>.card-conic</code></summary>


*Wrap content in an element with `.card-conic`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-conic" style="width:130px;height:90px"><div class="fx-card-conic-inner"><span style="font-size:1.3rem">🌀</span><span style="font-size:0.7rem;color:var(--text-dim)">Conic</span></div></div>
```


```css
.card-conic {
  position: relative;
  border-radius: 10px;
  padding: 2px;
  overflow: hidden;
  background: conic-gradient(from var(--conic-angle, 0deg), #3AB54A, #2dd4bf, #f97316, #ec4899, #3AB54A);
  animation: conicSpin 3s linear infinite;
}
@property --conic-angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}
@keyframes conicSpin { to { --conic-angle: 360deg; } }
.card-conic-inner {
  background: #161b22;
  border-radius: 8px;
  padding: 16px;
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 6px;
  color: #e2e8f0;
}
```

</details>

<details><summary><b>Glass Card</b> — <code>.card-glass-new</code></summary>


*Wrap content in an element with `.card-glass-new`. Repeat in a responsive grid for feature/pricing/testimonial sections.*


```html
<div class="fx-card-preview fx-card-glass-new"><span class="card-icon">🧊</span><span class="card-title-sm" style="color:rgba(255,255,255,0.7)">Glass</span></div>
```


```css
.card-glass-new {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
  color: #e2e8f0;
}
```

</details>


### Forms & Inputs  ·  8 components

_Styled inputs, focus states, floating labels. Pair every input with a visible label and a clear focus ring (accessibility-critical)._

**Pairs well with:** contact forms, quote forms, newsletter signups

<details><summary><b>Underline Focus</b> — <code>.input-underline</code></summary>


*Apply `.input-underline` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><input class="fx-input-underline" placeholder="Type here..."></div>
```


```css
.input-underline {
  background: transparent;
  border: none;
  border-bottom: 2px solid #30363d;
  color: #e2e8f0;
  padding: 8px 4px;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.3s;
}
.input-underline:focus { border-bottom-color: #3AB54A; }
```

</details>

<details><summary><b>Label Float</b> — <code>.input-float-group</code></summary>


*Apply `.input-float-group` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><div class="fx-input-float-group"><input class="fx-input-float" placeholder="Email"><span class="fx-input-float-label">EMAIL</span></div></div>
```


```css
.input-float-group { position: relative; }
.input-float {
  background: transparent;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;
  padding: 20px 10px 6px;
  font-size: 0.85rem;
  outline: none;
  width: 100%;
  transition: border-color 0.3s;
}
.input-float:focus { border-color: #3AB54A; }
.input-float-label {
  position: absolute;
  top: 6px; left: 10px;
  font-size: 0.65rem;
  color: #8b949e;
}
```

</details>

<details><summary><b>Glow Focus</b> — <code>.input-glow</code></summary>


*Apply `.input-glow` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><input class="fx-input-glow" placeholder="Type here..."></div>
```


```css
.input-glow {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;
  padding: 10px;
  font-size: 0.85rem;
  outline: none;
  transition: all 0.3s;
}
.input-glow:focus {
  border-color: #3AB54A;
  box-shadow: 0 0 10px rgba(58,181,74,0.4);
}
```

</details>

<details><summary><b>Outline Focus</b> — <code>.input-outline</code></summary>


*Apply `.input-outline` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><input class="fx-input-outline" placeholder="Type here..."></div>
```


```css
.input-outline {
  background: #161b22;
  border: 2px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;
  padding: 8px 10px;
  font-size: 0.85rem;
  outline: none;
  transition: all 0.3s;
}
.input-outline:focus {
  border-color: #3AB54A;
  box-shadow: 0 0 0 3px rgba(58,181,74,0.15);
}
```

</details>

<details><summary><b>Filled Background</b> — <code>.input-filled</code></summary>


*Apply `.input-filled` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><input class="fx-input-filled" placeholder="Type here..."></div>
```


```css
.input-filled {
  background: #21262d;
  border: none;
  border-bottom: 2px solid #30363d;
  border-radius: 6px 6px 0 0;
  color: #e2e8f0;
  padding: 12px 10px 8px;
  font-size: 0.85rem;
  outline: none;
  transition: all 0.3s;
}
.input-filled:focus {
  background: #30363d;
  border-bottom-color: #3AB54A;
}
```

</details>

<details><summary><b>Shake Input</b> — <code>.input-shake</code></summary>


*Apply `.input-shake` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><input class="fx-input-shake" value="Invalid!" onfocus="this.classList.add('shake');setTimeout(()=>this.classList.remove('shake'),500)"></div>
```


```css
.input-shake {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;
  padding: 10px;
  font-size: 0.85rem;
  outline: none;
  width: 140px;
  transition: all 0.3s;
}
.input-shake:focus { border-color: #3AB54A; }
.input-shake.shake {
  animation: inputShake 0.5s ease;
  border-color: #ff4444;
}
@keyframes inputShake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
```

</details>

<details><summary><b>Character Counter</b> — <code>.input-char-group</code></summary>


*Apply `.input-char-group` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><div class="fx-input-char-group"><input class="fx-input-char" value="Hello world" maxlength="20" oninput="updateCharCount(this)"><span class="fx-char-count">11/20</span></div></div>
```


```css
.input-char-group { position: relative; width: 140px; }
.input-char {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;
  padding: 10px;
  font-size: 0.85rem;
  outline: none;
  width: 100%;
  transition: border-color 0.3s;
}
.input-char:focus { border-color: #3AB54A; }
.char-count {
  text-align: right;
  font-size: 0.65rem;
  color: #8b949e;
  margin-top: 4px;
}
.char-count.warn { color: #f97316; }
.char-count.over { color: #ff4444; }
```

</details>

<details><summary><b>Password Toggle</b> — <code>.input-pw-group</code></summary>


*Apply `.input-pw-group` to an input/field. Pair with a visible `<label>` and keep the focus ring.*


```html
<div class="fx-form-preview"><div class="fx-input-pw-group"><input class="fx-input-pw" type="password" value="secret123"><button class="fx-pw-toggle" onclick="togglePw(this)">👁</button></div></div>
```


```css
.input-pw-group { position: relative; width: 140px; }
.input-pw {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;   padding: 10px 30px 10px 10px;
  font-size: 0.85rem;
  outline: none;
  width: 100%;
  transition: border-color 0.3s;
}
.input-pw:focus { border-color: #3AB54A; }
.pw-toggle {
  position: absolute;
  right: 8px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  color: #8b949e; cursor: pointer;
  font-size: 0.85rem;
  padding: 2px;
  transition: color 0.2s;
}
.pw-toggle:hover { color: #3AB54A; }
```

</details>


### Loaders & Spinners  ·  18 components

_Async feedback — page loads, form submits, data fetches. Always pair with a real loading state; never leave a button dead during async._

**Pairs well with:** buttons (loading state), data dashboards, skeleton screens

<details><summary><b>Circle Spinner</b> — <code>.spinner</code></summary>


*Show an element with `.spinner` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-spinner-circle"></div>
```


```css
.spinner {
  width: 40px; height: 40px;
  border: 4px solid #30363d;
  border-top-color: #3AB54A;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Bouncing Dots</b> — <code>.bounce-dots</code></summary>


*Show an element with `.bounce-dots` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-bounce-dots"><span></span><span></span><span></span></div>
```


```css
.bounce-dots { display: flex; gap: 8px; }
.bounce-dots span {
  width: 14px; height: 14px;
  background: #3AB54A;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.bounce-dots span:nth-child(1) { animation-delay: -0.32s; }
.bounce-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%,80%,100% { transform: scale(0); }
  40% { transform: scale(1); }
}
```

</details>

<details><summary><b>Rotating Square</b> — <code>.square-spin</code></summary>


*Show an element with `.square-spin` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-square-spin"></div>
```


```css
.square-spin {
  width: 40px; height: 40px;
  background: #3AB54A;
  animation: sqSpin 1.2s ease infinite;
}
@keyframes sqSpin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Pulse Ring</b> — <code>.pulse-ring</code></summary>


*Show an element with `.pulse-ring` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-pulse-ring"></div>
```


```css
.pulse-ring {
  width: 40px; height: 40px;
  border-radius: 50%;
  background: #3AB54A;
  position: relative;
}
.pulse-ring::before, .pulse-ring::after {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 3px solid #3AB54A;
  animation: pulseRing 1.5s ease-out infinite;
}
.pulse-ring::after { animation-delay: 0.5s; }
@keyframes pulseRing {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(1.3); opacity: 0; }
}
```

</details>

<details><summary><b>Bar Loader</b> — <code>.bar-loader</code></summary>


*Show an element with `.bar-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-bar-loader"></div>
```


```css
.bar-loader {
  width: 120px; height: 6px;
  background: #30363d;
  border-radius: 3px;
  overflow: hidden;
}
.bar-loader::after {
  content: '';
  display: block;
  width: 40%; height: 100%;
  background: #3AB54A;
  border-radius: 3px;
  animation: barMove 1.5s ease infinite;
}
@keyframes barMove {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
```

</details>

<details><summary><b>Flip Loader</b> — <code>.flip-loader</code></summary>


*Show an element with `.flip-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-flip-loader"></div>
```


```css
.flip-loader {
  width: 40px; height: 40px;
  background: #3AB54A;
  animation: flipLoad 1.2s ease infinite;
}
@keyframes flipLoad {
  0% { transform: perspective(160px) rotateX(0); }
  50% { transform: perspective(160px) rotateX(180deg); }
  100% { transform: perspective(160px) rotateX(360deg); }
}
```

</details>

<details><summary><b>Dot Wave</b> — <code>.dot-wave</code></summary>


*Show an element with `.dot-wave` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-dot-wave"><span></span><span></span><span></span><span></span><span></span></div>
```


```css
.dot-wave { display: flex; gap: 6px; }
.dot-wave span {
  width: 12px; height: 12px;
  background: #3AB54A;
  border-radius: 50%;
  animation: dotWave 1.2s ease-in-out infinite;
}
.dot-wave span:nth-child(2) { animation-delay: 0.1s; }
.dot-wave span:nth-child(3) { animation-delay: 0.2s; }
.dot-wave span:nth-child(4) { animation-delay: 0.3s; }
.dot-wave span:nth-child(5) { animation-delay: 0.4s; }
@keyframes dotWave {
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-18px); }
}
```

</details>

<details><summary><b>Square Spin</b> — <code>.square-spin3d</code></summary>


*Show an element with `.square-spin3d` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-square-spin3d"></div>
```


```css
.square-spin3d {
  width: 40px; height: 40px;
  background: #3AB54A;
  animation: sqSpin3d 2.4s ease infinite;
}
@keyframes sqSpin3d {
  0% { transform: perspective(120px) rotateX(0) rotateY(0); }
  25% { transform: perspective(120px) rotateX(180deg) rotateY(0); }
  50% { transform: perspective(120px) rotateX(180deg) rotateY(180deg); }
  75% { transform: perspective(120px) rotateX(0) rotateY(180deg); }
  100% { transform: perspective(120px) rotateX(0) rotateY(360deg); }
}
```

</details>

<details><summary><b>Orbit Spinner</b> — <code>.orbit-spinner</code></summary>


*Show an element with `.orbit-spinner` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-orbit-spinner"></div>
```


```css
.orbit-spinner {
  width: 50px; height: 50px;
  position: relative;
}
.orbit-spinner::before, .orbit-spinner::after {
  content: '';
  position: absolute;
  border-radius: 50%;
}
.orbit-spinner::before {
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #3AB54A;
  animation: spin 1s linear infinite;
}
.orbit-spinner::after {
  width: 8px; height: 8px;
  background: #3AB54A;
  border-radius: 50%;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}
@keyframes spin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Cube Loader</b> — <code>.cube-loader</code></summary>


*Show an element with `.cube-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-cube-loader"><div class="cube-face"></div><div class="cube-face"></div><div class="cube-face"></div><div class="cube-face"></div><div class="cube-face"></div><div class="cube-face"></div></div>
```


```css
.cube-loader {
  width: 40px; height: 40px;
  transform-style: preserve-3d;
  animation: cubeRotate 1.8s ease-in-out infinite;
}
.cube-face {
  position: absolute;
  width: 40px; height: 40px;
  border: 2px solid #3AB54A;
  background: rgba(58,181,74,0.15);
  border-radius: 4px;
}
.cube-face:nth-child(1) { transform: translateZ(20px); }
.cube-face:nth-child(2) { transform: rotateY(180deg) translateZ(20px); }
.cube-face:nth-child(3) { transform: rotateY(90deg) translateZ(20px); }
.cube-face:nth-child(4) { transform: rotateY(-90deg) translateZ(20px); }
.cube-face:nth-child(5) { transform: rotateX(90deg) translateZ(20px); }
.cube-face:nth-child(6) { transform: rotateX(-90deg) translateZ(20px); }
@keyframes cubeRotate {
  0% { transform: rotateX(0) rotateY(0); }
  25% { transform: rotateX(90deg) rotateY(90deg); }
  50% { transform: rotateX(180deg) rotateY(180deg); }
  75% { transform: rotateX(270deg) rotateY(270deg); }
  100% { transform: rotateX(360deg) rotateY(360deg); }
}
```

</details>

<details><summary><b>DNA Helix Loader</b> — <code>.dna-loader</code></summary>


*Show an element with `.dna-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-dna-loader"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
```


```css
.dna-loader { display: flex; gap: 4px; align-items: center; height: 50px; }
.dna-loader span {
  width: 8px; height: 8px;
  border-radius: 50%;
  animation: dnaWave 1.2s ease-in-out infinite;
}
.dna-loader span:nth-child(odd) { background: #3AB54A; }
.dna-loader span:nth-child(even) { background: #2dd4bf; }
@keyframes dnaWave {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-16px) scale(0.6); }
}
.dna-loader span:nth-child(1) { animation-delay: 0s; }
.dna-loader span:nth-child(2) { animation-delay: 0.1s; }
.dna-loader span:nth-child(3) { animation-delay: 0.2s; }
.dna-loader span:nth-child(4) { animation-delay: 0.3s; }
.dna-loader span:nth-child(5) { animation-delay: 0.4s; }
.dna-loader span:nth-child(6) { animation-delay: 0.5s; }
.dna-loader span:nth-child(7) { animation-delay: 0.6s; }
.dna-loader span:nth-child(8) { animation-delay: 0.7s; }
```

</details>

<details><summary><b>Clock Loader</b> — <code>.clock-loader</code></summary>


*Show an element with `.clock-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-clock-loader"></div>
```


```css
.clock-loader {
  width: 40px; height: 40px;
  border-radius: 50%;
  border: 3px solid #30363d;
  position: relative;
}
.clock-loader::before {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  width: 2px; height: 12px;
  background: #3AB54A;
  transform-origin: bottom center;
  animation: clockTick 1s ease-in-out infinite;
}
.clock-loader::after {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  width: 2px; height: 8px;
  background: #2dd4bf;
  transform-origin: bottom center;
  animation: clockTick 6s linear infinite;
}
@keyframes clockTick { to { transform: translate(-50%, -100%) rotate(360deg); } }
```

</details>

<details><summary><b>Ring Dots</b> — <code>.ring-dots</code></summary>


*Show an element with `.ring-dots` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-ring-dots"><span></span><span></span><span></span><span></span></div>
```


```css
.ring-dots {
  width: 50px; height: 50px;
  position: relative;
  animation: spin 2s linear infinite;
}
.ring-dots span {
  position: absolute;
  width: 8px; height: 8px;
  background: #3AB54A;
  border-radius: 50%;
}
.ring-dots span:nth-child(1) { top: 0; left: 50%; transform: translateX(-50%); }
.ring-dots span:nth-child(2) { top: 50%; right: 0; transform: translateY(-50%); }
.ring-dots span:nth-child(3) { bottom: 0; left: 50%; transform: translateX(-50%); }
.ring-dots span:nth-child(4) { top: 50%; left: 0; transform: translateY(-50%); }
@keyframes spin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Beat Loader</b> — <code>.beat-loader</code></summary>


*Show an element with `.beat-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-beat-loader"><span></span><span></span><span></span></div>
```


```css
.beat-loader { display: flex; gap: 6px; align-items: center; }
.beat-loader span {
  width: 14px; height: 14px;
  background: #3AB54A;
  border-radius: 50%;
  animation: beatPulse 1.4s ease-in-out infinite;
}
.beat-loader span:nth-child(1) { animation-delay: 0s; }
.beat-loader span:nth-child(2) { animation-delay: 0.2s; }
.beat-loader span:nth-child(3) { animation-delay: 0.4s; }
@keyframes beatPulse {
  0%, 100% { transform: scale(0.4); opacity: 0.4; }
  50% { transform: scale(1); opacity: 1; }
}
```

</details>

<details><summary><b>Hourglass Loader</b> — <code>.hourglass-loader</code></summary>


*Show an element with `.hourglass-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-hourglass"></div>
```


```css
.hourglass-loader {
  width: 30px; height: 50px;
  position: relative;
  animation: hourglassFlip 2.5s ease-in-out infinite;
}
.hourglass-loader::before, .hourglass-loader::after {
  content: '';
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  border-left: 15px solid transparent;
  border-right: 15px solid transparent;
}
.hourglass-loader::before { top: 0; border-top: 25px solid #3AB54A; }
.hourglass-loader::after { bottom: 0; border-bottom: 25px solid rgba(58,181,74,0.4); }
@keyframes hourglassFlip {
  0%, 45% { transform: rotate(0); }
  50%, 95% { transform: rotate(180deg); }
  100% { transform: rotate(360deg); }
}
```

</details>

<details><summary><b>Pendulum Loader</b> — <code>.pendulum-loader</code></summary>


*Show an element with `.pendulum-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-pendulum"></div>
```


```css
.pendulum-loader {
  width: 2px; height: 50px;
  background: #30363d;
  position: relative;
  transform-origin: top center;
  animation: pendulumSwing 1.5s ease-in-out infinite;
  margin: 0 auto;
}
.pendulum-loader::after {
  content: '';
  position: absolute;
  bottom: -8px; left: 50%;
  transform: translateX(-50%);
  width: 18px; height: 18px;
  background: #3AB54A;
  border-radius: 50%;
}
@keyframes pendulumSwing {
  0%, 100% { transform: rotate(30deg); }
  50% { transform: rotate(-30deg); }
}
```

</details>

<details><summary><b>Atom Loader</b> — <code>.atom-loader</code></summary>


*Show an element with `.atom-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-atom-loader"><span class="atom-core"></span><div class="atom-orbit"></div><div class="atom-orbit"></div><div class="atom-orbit"></div></div>
```


```css
.atom-loader {
  width: 60px; height: 60px;
  position: relative;
}
.atom-core {
  position: absolute;
  width: 10px; height: 10px;
  background: #3AB54A;
  border-radius: 50%;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}
.atom-orbit {
  position: absolute;
  inset: 0;
  border: 2px solid transparent;
  border-top-color: rgba(58,181,74,0.5);
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}
.atom-orbit:nth-child(2) { transform: rotate(60deg); animation-duration: 1.8s; border-top-color: rgba(45,212,191,0.5); }
.atom-orbit:nth-child(3) { transform: rotate(120deg); animation-duration: 2.1s; border-top-color: rgba(249,115,22,0.5); }
@keyframes spin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Snake Loader</b> — <code>.snake-loader</code></summary>


*Show an element with `.snake-loader` while async work runs; hide on complete. Disable the triggering button meanwhile.*


```html
<div class="fx-snake-loader"><span></span><span></span><span></span><span></span><span></span></div>
```


```css
.snake-loader { display: flex; gap: 6px; }
.snake-loader span {
  width: 12px; height: 12px;
  background: #3AB54A;
  border-radius: 50%;
  animation: snakeMove 1.5s ease-in-out infinite;
}
.snake-loader span:nth-child(1) { animation-delay: 0s; }
.snake-loader span:nth-child(2) { animation-delay: 0.15s; }
.snake-loader span:nth-child(3) { animation-delay: 0.3s; }
.snake-loader span:nth-child(4) { animation-delay: 0.45s; }
.snake-loader span:nth-child(5) { animation-delay: 0.6s; }
@keyframes snakeMove {
  0%, 100% { transform: translateY(0) scale(1); opacity: 1; }
  25% { transform: translateY(-20px) scale(0.6); opacity: 0.4; }
  50% { transform: translateY(0) scale(1); opacity: 1; }
  75% { transform: translateY(8px) scale(0.8); opacity: 0.7; }
}
```

</details>


### Text & Headings  ·  20 components

_Hero headlines, animated section titles, gradient/typewriter emphasis. Use sparingly — one animated headline per viewport, not every line._

**Pairs well with:** hero sections, section intros, feature highlights

<details><summary><b>Gradient Text</b> — <code>.text-gradient</code></summary>


*Apply `.text-gradient` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-gradient">Gradient</span>
```


```css
.text-gradient {
  font-weight: 700;
  font-size: 2rem;
  background: linear-gradient(135deg, #3AB54A, #2dd4bf, #f97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

</details>

<details><summary><b>Glitch Text</b> — <code>.text-glitch</code></summary>


*Apply `.text-glitch` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-glitch">Glitch</span>
```


```css
.text-glitch {
  font-weight: 700;
  color: #e2e8f0;
  animation: glitch 2s infinite;
}
@keyframes glitch {
  0%,100% { text-shadow: none; }
  2% { text-shadow: -2px 0 #ff0040, 2px 0 #00ffff; }
  4% { text-shadow: 2px 0 #ff0040, -2px 0 #00ffff; }
  6% { text-shadow: none; }
}
```

</details>

<details><summary><b>Typewriter</b> — <code>.text-typewriter</code></summary>


*Apply `.text-typewriter` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-typewriter">Typewriter</span>
```


```css
.text-typewriter {
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  border-right: 2px solid #3AB54A;
  animation: type 3s steps(12) infinite, blink 0.7s step-end infinite;
  max-width: 200px;
}
@keyframes type {
  0%,10% { width: 0; }
  50%,70% { width: 12ch; }
  90%,100% { width: 0; }
}
@keyframes blink { 50% { border-color: transparent; } }
```

</details>

<details><summary><b>Neon Text</b> — <code>.text-neon</code></summary>


*Apply `.text-neon` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-neon">Neon</span>
```


```css
.text-neon {
  font-weight: 700;
  color: #3AB54A;
  text-shadow:
    0 0 7px rgba(58,181,74,0.4),
    0 0 10px rgba(58,181,74,0.4),
    0 0 21px rgba(58,181,74,0.4),
    0 0 42px rgba(58,181,74,0.3);
}
```

</details>

<details><summary><b>Stroke Text</b> — <code>.text-stroke</code></summary>


*Apply `.text-stroke` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-stroke">Stroke</span>
```


```css
.text-stroke {
  font-weight: 700;
  -webkit-text-stroke: 2px #3AB54A;
  color: transparent;
}
```

</details>

<details><summary><b>Shadow Stack Text</b> — <code>.text-shadow-stack</code></summary>


*Apply `.text-shadow-stack` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-shadow-stack">Stack</span>
```


```css
.text-shadow-stack {
  font-weight: 700;
  color: #e2e8f0;
  text-shadow:
    1px 1px 0 #3AB54A,
    2px 2px 0 rgba(58,181,74,0.8),
    3px 3px 0 rgba(58,181,74,0.6),
    4px 4px 0 rgba(58,181,74,0.4),
    5px 5px 0 rgba(58,181,74,0.2);
}
```

</details>

<details><summary><b>Underline Slide</b> — <code>.text-underline</code></summary>


*Apply `.text-underline` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-underline" style="cursor:pointer">Hover Me</span>
```


```css
.text-underline {
  font-weight: 700;
  position: relative;
}
.text-underline::after {
  content: '';
  position: absolute;
  bottom: -4px; left: 0;
  width: 100%; height: 3px;
  background: #3AB54A;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.4s;
}
.text-underline:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}
```

</details>

<details><summary><b>Text Reveal</b> — <code>.text-reveal</code></summary>


*Apply `.text-reveal` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-reveal">Reveal</span>
```


```css
.text-reveal {
  font-weight: 700;
  position: relative;
  overflow: hidden;
  display: inline-block;
}
.text-reveal::after {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: #3AB54A;
  animation: textReveal 3s infinite;
}
@keyframes textReveal {
  0% { transform: translateX(-101%); }
  40% { transform: translateX(0); }
  60% { transform: translateX(0); }
  100% { transform: translateX(101%); }
}
```

</details>

<details><summary><b>Rainbow Text</b> — <code>.text-rainbow</code></summary>


*Apply `.text-rainbow` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-rainbow">Rainbow</span>
```


```css
.text-rainbow {
  font-weight: 700;
  font-size: 1.6rem;
  background: linear-gradient(90deg, #ff0000, #ff7700, #ffff00, #00ff00, #0000ff, #8b00ff, #ff0000);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: rainbowShift 3s linear infinite;
}
@keyframes rainbowShift { to { background-position: 200% center; } }
```

</details>

<details><summary><b>Blink Cursor Text</b> — <code>.text-blink-cursor</code></summary>


*Apply `.text-blink-cursor` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-blink-cursor">Code mode</span>
```


```css
.text-blink-cursor {
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  border-right: 2px solid #3AB54A;
  animation: typeStep 4s steps(10) infinite, blink 0.7s step-end infinite;
  max-width: 170px;
  font-size: 1.6rem;
}
@keyframes typeStep {
  0%,10% { width: 0; }
  40%,60% { width: 10ch; }
  90%,100% { width: 0; }
}
@keyframes blink { 50% { border-color: transparent; } }
```

</details>

<details><summary><b>Wave Text</b> — <code>.text-wave</code></summary>


*Apply `.text-wave` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-wave"><span>W</span><span>a</span><span>v</span><span>e</span><span>!</span></span>
```


```css
.text-wave { display: inline-flex; font-weight: 700; font-size: 1.6rem; }
.text-wave span {
  display: inline-block;
  animation: textWave 1.5s ease-in-out infinite;
  color: #e2e8f0;
}
.text-wave span:nth-child(1) { animation-delay: 0s; }
.text-wave span:nth-child(2) { animation-delay: 0.1s; }
.text-wave span:nth-child(3) { animation-delay: 0.2s; }
.text-wave span:nth-child(4) { animation-delay: 0.3s; }
.text-wave span:nth-child(5) { animation-delay: 0.4s; }
@keyframes textWave {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
```

</details>

<details><summary><b>Strike Through Text</b> — <code>.text-strike</code></summary>


*Apply `.text-strike` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-strike" style="cursor:pointer">Hover Me</span>
```


```css
.text-strike {
  font-weight: 700;
  position: relative;
  color: #e2e8f0;
  cursor: pointer;
  display: inline-block;
}
.text-strike::after {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  width: 100%; height: 3px;
  background: #ff4444;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s;
}
.text-strike:hover::after { transform: scaleX(1); }
```

</details>

<details><summary><b>Highlight Text</b> — <code>.text-highlight</code></summary>


*Apply `.text-highlight` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-highlight" style="cursor:pointer">Hover Me</span>
```


```css
.text-highlight {
  font-weight: 700;
  position: relative;
  color: #e2e8f0;
  padding: 0 4px;
  cursor: pointer;
  display: inline-block;
}
.text-highlight::after {
  content: '';
  position: absolute;
  left: -4px; bottom: 0;
  width: calc(100% + 8px);
  height: 35%;
  background: rgba(58,181,74,0.35);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.5s;
  z-index: -1;
}
.text-highlight:hover::after { transform: scaleX(1); }
```

</details>

<details><summary><b>Retro Text</b> — <code>.text-retro</code></summary>


*Apply `.text-retro` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-retro">RETRO</span>
```


```css
.text-retro {
  font-weight: 900;
  font-size: 1.6rem;
  color: #3AB54A;
  text-shadow:
    3px 3px 0 #0d1117,
    -1px -1px 0 rgba(58,181,74,0.6),
    1px -1px 0 rgba(45,212,191,0.4),
    -1px 1px 0 rgba(249,115,22,0.4);
  letter-spacing: 2px;
}
```

</details>

<details><summary><b>Bounce Text</b> — <code>.text-bounce</code></summary>


*Apply `.text-bounce` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-bounce">Bounce!</span>
```


```css
.text-bounce {
  font-weight: 700;
  font-size: 1.6rem;
  display: inline-block;
  animation: textBounce 1s ease infinite;
  color: #3AB54A;
}
@keyframes textBounce {
  0%, 100% { transform: translateY(0); }
  30% { transform: translateY(-20px); }
  50% { transform: translateY(0); }
  65% { transform: translateY(-8px); }
  80% { transform: translateY(0); }
}
```

</details>

<details><summary><b>Blur In Text</b> — <code>.text-blur-in</code></summary>


*Apply `.text-blur-in` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-blur-in">Blur In</span>
```


```css
.text-blur-in {
  font-weight: 700;
  font-size: 1.6rem;
  color: #e2e8f0;
  animation: blurIn 2s ease-in-out infinite alternate;
}
@keyframes blurIn {
  0% { filter: blur(10px); opacity: 0; }
  50% { filter: blur(0); opacity: 1; }
  100% { filter: blur(5px); opacity: 0.7; }
}
```

</details>

<details><summary><b>Scramble Text</b> — <code>.text-scramble</code></summary>


*Apply `.text-scramble` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-scramble"><span class="fx-text-scramble-inner">D3crypt</span></span>
```


```css
.text-scramble {
  font-weight: 700;
  font-size: 1.4rem;
  color: #3AB54A;
  font-family: 'JetBrains Mono', monospace;
  animation: scrambleChars 3s step-end infinite;
}
@keyframes scrambleChars {
  0% { opacity: 1; }
  10% { opacity: 0.8; transform: skewX(5deg); }
  20% { opacity: 1; transform: skewX(-3deg); }
  30% { opacity: 0.6; }
  40%, 100% { opacity: 1; transform: none; }
}
```

</details>

<details><summary><b>Animated Gradient Text</b> — <code>.text-anim-gradient</code></summary>


*Apply `.text-anim-gradient` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-anim-gradient">Gradient</span>
```


```css
.text-anim-gradient {
  font-weight: 700;
  font-size: 1.6rem;
  background: linear-gradient(90deg, #3AB54A, #2dd4bf, #f97316, #ec4899, #3AB54A);
  background-size: 300% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientFlow 4s ease infinite;
}
@keyframes gradientFlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

</details>

<details><summary><b>Glitch Effect</b> — <code>.text-glitch-advanced</code></summary>


*Apply `.text-glitch-advanced` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-glitch-advanced">GLITCH</span>
```


```css
.text-glitch-advanced {
  position: relative;
  color: #e2e8f0;
  font-weight: 700;
  animation: glitchAdvanced 3s infinite;
}
@keyframes glitchAdvanced {
  0%, 100% { text-shadow: none; transform: none; }
  1% { text-shadow: -2px 0 #ff0040, 2px 0 #00ffff; transform: translateX(-1px); }
  2% { text-shadow: 2px 0 #ff0040, -2px 0 #00ffff; transform: translateX(1px); }
  3% { text-shadow: none; transform: none; }
  20% { text-shadow: -1px 0 rgba(255,0,64,0.6), 1px 0 rgba(0,255,255,0.6); }
  21% { text-shadow: none; }
  40% { text-shadow: -3px 0 #ff0040, 3px 0 #00ffff; transform: skewX(-2deg); }
  41% { text-shadow: 3px 0 #ff0040, -3px 0 #00ffff; transform: skewX(2deg); }
  42% { text-shadow: none; transform: none; }
  80% { text-shadow: -1px 0 rgba(255,0,64,0.4), 1px 0 rgba(0,255,255,0.4); transform: translateX(1px); }
  81% { text-shadow: none; transform: none; }
}
```

</details>

<details><summary><b>Neon Flicker</b> — <code>.text-neon-flicker</code></summary>


*Apply `.text-neon-flicker` to a heading/`<span>`. Limit to one animated headline per viewport.*


```html
<span class="fx-text fx-text-neon-flicker">Neon</span>
```


```css
.text-neon-flicker {
  color: #ff6ec7;
  font-weight: 700;
  text-shadow: 0 0 7px rgba(255,110,199,0.6), 0 0 10px rgba(255,110,199,0.4), 0 0 21px rgba(255,110,199,0.3), 0 0 42px rgba(255,110,199,0.2);
  animation: neonFlicker 3s infinite;
}
@keyframes neonFlicker {
  0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
    opacity: 1;
    text-shadow: 0 0 7px rgba(255,110,199,0.6), 0 0 10px rgba(255,110,199,0.4), 0 0 21px rgba(255,110,199,0.3), 0 0 42px rgba(255,110,199,0.2);
  }
  20%, 24%, 55% {
    opacity: 0.4;
    text-shadow: none;
  }
}
```

</details>


### Backgrounds & Sections  ·  10 components

_Full-section ambiance — hero gradients, animated meshes, particle fields. Keep behind content with sufficient text contrast (4.5:1)._

**Pairs well with:** hero sections, CTA bands, page backgrounds

<details><summary><b>Gradient Mesh</b> — <code>.bg-mesh</code></summary>


*Place an element with `.bg-mesh` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-mesh"></div>
```


```css
.bg-mesh {
  background:
    radial-gradient(at 20% 30%, rgba(58,181,74,0.4) 0, transparent 50%),
    radial-gradient(at 80% 70%, rgba(45,212,191,0.3) 0, transparent 50%),
    radial-gradient(at 50% 50%, rgba(249,115,22,0.2) 0, transparent 50%),
    #0d1117;
}
```

</details>

<details><summary><b>Animated Gradient</b> — <code>.bg-anim-grad</code></summary>


*Place an element with `.bg-anim-grad` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-anim-grad"></div>
```


```css
.bg-anim-grad {
  background: linear-gradient(-45deg, #3AB54A, #2dd4bf, #f97316, #ec4899);
  background-size: 400% 400%;
  animation: gradBg 6s ease infinite;
}
@keyframes gradBg {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

</details>

<details><summary><b>Dot Pattern</b> — <code>.bg-dots</code></summary>


*Place an element with `.bg-dots` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-dots"></div>
```


```css
.bg-dots {
  background-image: radial-gradient(circle, #30363d 1px, transparent 1px);
  background-size: 20px 20px;
}
```

</details>

<details><summary><b>Wave Pattern</b> — <code>.bg-wave</code></summary>


*Place an element with `.bg-wave` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-wave"></div>
```


```css
.bg-wave {
  background: linear-gradient(135deg, rgba(58,181,74,0.15), transparent);
  overflow: hidden;
  position: relative;
}
.bg-wave::before {
  content: '';
  position: absolute;
  width: 300%; height: 300%;
  top: -100%; left: -50%;
  background: repeating-radial-gradient(
    circle at 50% 50%,
    transparent 0, transparent 18px,
    rgba(58,181,74,0.08) 19px,
    rgba(58,181,74,0.08) 20px
  );
  animation: waveRotate 20s linear infinite;
}
@keyframes waveRotate { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Geometric Pattern</b> — <code>.bg-geo</code></summary>


*Place an element with `.bg-geo` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-geo"></div>
```


```css
.bg-geo {
  background-color: #0d1117;
  background-image:
    linear-gradient(30deg, rgba(58,181,74,0.15) 12%, transparent 12.5%, transparent 87%, rgba(58,181,74,0.15) 87.5%),
    linear-gradient(150deg, rgba(58,181,74,0.15) 12%, transparent 12.5%, transparent 87%, rgba(58,181,74,0.15) 87.5%),
    linear-gradient(30deg, rgba(58,181,74,0.15) 12%, transparent 12.5%, transparent 87%, rgba(58,181,74,0.15) 87.5%),
    linear-gradient(150deg, rgba(58,181,74,0.15) 12%, transparent 12.5%, transparent 87%, rgba(58,181,74,0.15) 87.5%);
  background-size: 40px 70px;
  background-position: 0 0, 0 0, 20px 35px, 20px 35px;
}
```

</details>

<details><summary><b>Starfield</b> — <code>.bg-starfield</code></summary>


*Place an element with `.bg-starfield` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-starfield"></div>
```


```css
.bg-starfield {
  background: #0a0a14;
  position: relative;
  overflow: hidden;
}
.bg-starfield::before {
  content: '';
  position: absolute;
  width: 2px; height: 2px;
  background: white;
  border-radius: 50%;
  box-shadow:
    20px 30px 0 0 rgba(255,255,255,0.8),
    60px 10px 0 0 rgba(255,255,255,0.6),
    100px 50px 0 0 rgba(255,255,255,0.9),
    40px 80px 0 0 rgba(255,255,255,0.5),
    130px 20px 0 0 rgba(255,255,255,0.7),
    10px 110px 0 0 rgba(255,255,255,0.6),
    80px 130px 0 0 rgba(255,255,255,0.8);
  animation: starDrift 20s linear infinite;
}
@keyframes starDrift { to { transform: translateY(-40px); } }
```

</details>

<details><summary><b>Bubble Background</b> — <code>.bg-bubbles</code></summary>


*Place an element with `.bg-bubbles` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-bubbles"></div>
```


```css
.bg-bubbles {
  background: linear-gradient(135deg, #0d1117, #161b22);
  position: relative;
  overflow: hidden;
}
.bg-bubbles::before, .bg-bubbles::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(58,181,74,0.15);
  animation: bubbleRise 4s ease-in infinite;
}
.bg-bubbles::before { width: 20px; height: 20px; left: 20%; bottom: -30px; }
.bg-bubbles::after { width: 14px; height: 14px; left: 60%; bottom: -20px; animation-delay: 1s; }
@keyframes bubbleRise {
  0% { transform: translateY(0) scale(1); opacity: 0.8; }
  100% { transform: translateY(-180px) scale(0.3); opacity: 0; }
}
```

</details>

<details><summary><b>Zigzag Pattern</b> — <code>.bg-zigzag</code></summary>


*Place an element with `.bg-zigzag` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-zigzag"></div>
```


```css
.bg-zigzag {
  background-color: #0d1117;
  background-image:
    linear-gradient(135deg, rgba(58,181,74,0.15) 25%, transparent 25%),
    linear-gradient(225deg, rgba(58,181,74,0.15) 25%, transparent 25%),
    linear-gradient(45deg, rgba(58,181,74,0.15) 25%, transparent 25%),
    linear-gradient(315deg, rgba(58,181,74,0.15) 25%, transparent 25%);
  background-position: 10px 0, 10px 0, 0 0, 0 0;
  background-size: 20px 20px;
  background-repeat: repeat-x;
}
```

</details>

<details><summary><b>Checkerboard</b> — <code>.bg-checker</code></summary>


*Place an element with `.bg-checker` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-checker"></div>
```


```css
.bg-checker {
  background-color: #0d1117;
  background-image:
    linear-gradient(45deg, rgba(58,181,74,0.12) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(58,181,74,0.12) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(58,181,74,0.12) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(58,181,74,0.12) 75%);
  background-size: 30px 30px;
  background-position: 0 0, 0 15px, 15px -15px, -15px 0px;
}
```

</details>

<details><summary><b>Noise Texture</b> — <code>.bg-noise</code></summary>


*Place an element with `.bg-noise` behind a section (position it absolutely / as the section bg). Verify text contrast on top.*


```html
<div class="fx-bg-preview fx-bg-noise"></div>
```


```css
.bg-noise {
  background-color: #0d1117;
  background-image:
  url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.15'/%3E%3C/svg%3E");
  background-size: 200px 200px;
}
```

</details>


### Hover & Interaction  ·  13 components

_Micro-interactions on cards/links/images that reward the cursor. Desktop polish; ensure a tap-friendly fallback on mobile._

**Pairs well with:** cards, image galleries, nav links, feature tiles

<details><summary><b>Scale Up</b> — <code>.hover-scale</code></summary>


*Add `.hover-scale` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-scale">Scale</div>
```


```css
.hover-scale {
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  transition: all 0.3s;
  cursor: pointer;
}
.hover-scale:hover {
  transform: scale(1.15);
  border-color: #3AB54A;
}
```

</details>

<details><summary><b>Background Slide</b> — <code>.hover-bgslide</code></summary>


*Add `.hover-bgslide` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-bgslide">Slide</div>
```


```css
.hover-bgslide {
  position: relative;
  overflow: hidden;
  z-index: 1;
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  transition: all 0.3s;
  cursor: pointer;
}
.hover-bgslide::before {
  content: '';
  position: absolute;
  inset: 0;
  background: #3AB54A;
  transform: translateY(100%);
  transition: transform 0.3s;
  z-index: -1;
}
.hover-bgslide:hover::before { transform: translateY(0); }
.hover-bgslide:hover { color: #000; border-color: #3AB54A; }
```

</details>

<details><summary><b>Border Draw</b> — <code>.hover-border-draw</code></summary>


*Add `.hover-border-draw` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-border-draw">Draw</div>
```


```css
.hover-border-draw {
  position: relative;
  border-color: transparent;
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  transition: all 0.3s;
  cursor: pointer;
}
.hover-border-draw:hover {
  border-color: #3AB54A;
  box-shadow: 0 0 10px rgba(58,181,74,0.3);
}
```

</details>

<details><summary><b>Icon Morph</b> — <code>.hover-morph</code></summary>


*Add `.hover-morph` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-morph">⚡</div>
```


```css
.hover-morph {
  font-size: 2rem;
  color: #8b949e;
  transition: all 0.3s;
  cursor: pointer;
}
.hover-morph:hover {
  color: #3AB54A;
  transform: rotate(180deg) scale(1.2);
}
```

</details>

<details><summary><b>Color Shift</b> — <code>.hover-colorshift</code></summary>


*Add `.hover-colorshift` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-colorshift">Shift</div>
```


```css
.hover-colorshift {
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  transition: all 0.3s;
  cursor: pointer;
}
.hover-colorshift:hover {
  background: #3AB54A;
  color: #000;
  border-color: #3AB54A;
}
```

</details>

<details><summary><b>Shadow Pop</b> — <code>.hover-shadowpop</code></summary>


*Add `.hover-shadowpop` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-shadowpop">Pop</div>
```


```css
.hover-shadowpop {
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  transition: all 0.3s;
  cursor: pointer;
}
.hover-shadowpop:hover {
  box-shadow: 0 0 0 4px rgba(58,181,74,0.15), 0 8px 20px rgba(58,181,74,0.3);
  transform: translateY(-4px);
}
```

</details>

<details><summary><b>Curl Hover</b> — <code>.hover-curl</code></summary>


*Add `.hover-curl` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-curl" style="position:relative">Curl</div>
```


```css
.hover-curl {
  width: 90px; height: 90px;
  position: relative;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.4s;
}
.hover-curl::after {
  content: '';
  position: absolute;
  bottom: 0; right: 0;
  width: 0; height: 0;
  background: linear-gradient(135deg, rgba(58,181,74,0.3), rgba(0,0,0,0.3));
  border-radius: 0 0 10px 0;
  transition: width 0.4s, height 0.4s;
}
.hover-curl:hover::after { width: 30px; height: 30px; }
```

</details>

<details><summary><b>Blur Hover</b> — <code>.hover-blur</code></summary>


*Add `.hover-blur` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-blur">Focus</div>
```


```css
.hover-blur {
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: #8b949e;
  filter: blur(2px);
  transition: all 0.4s;
  cursor: pointer;
}
.hover-blur:hover {
  filter: blur(0);
  border-color: #3AB54A;
  box-shadow: 0 0 20px rgba(58,181,74,0.4);
}
```

</details>

<details><summary><b>Circle Reveal</b> — <code>.hover-circle-reveal</code></summary>


*Add `.hover-circle-reveal` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-circle-reveal" style="position:relative;overflow:hidden">Reveal</div>
```


```css
.hover-circle-reveal {
  width: 90px; height: 90px;
  position: relative;
  overflow: hidden;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  display: flex;
  align-items: center;   justify-content: center;
  font-size: 0.75rem;
  color: #8b949e;
  cursor: pointer;
}
.hover-circle-reveal::after {
  content: 'REVEALED';
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3AB54A;
  color: #000;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 50%;
  width: 0; height: 0;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: all 0.5s ease;
}
.hover-circle-reveal:hover::after {
  width: 200%; height: 200%;
  opacity: 1;
  border-radius: 10px;
}
```

</details>

<details><summary><b>Line Sweep</b> — <code>.hover-line-sweep</code></summary>


*Add `.hover-line-sweep` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-line-sweep" style="position:relative;overflow:hidden">Sweep</div>
```


```css
.hover-line-sweep {
  width: 90px; height: 90px;
  position: relative;
  overflow: hidden;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: #8b949e;
  cursor: pointer;
}
.hover-line-sweep::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 3px;
  background: #3AB54A;
  box-shadow: 0 0 15px rgba(58,181,74,0.4);
  transition: left 0.5s;
}
.hover-line-sweep:hover::after { left: 100%; }
```

</details>

<details><summary><b>Glow Expand</b> — <code>.hover-glow-expand</code></summary>


*Add `.hover-glow-expand` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-item fx-hover-glow-expand" style="position:relative;overflow:hidden">Glow</div>
```


```css
.hover-glow-expand {
  width: 90px; height: 90px;
  position: relative;
  overflow: hidden;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: #8b949e;
  transition: all 0.4s;
  cursor: pointer;
}
.hover-glow-expand::after {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  width: 10px; height: 10px;
  background: radial-gradient(circle, rgba(58,181,74,0.4), transparent);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: all 0.5s;
}
.hover-glow-expand:hover::after {
  width: 150px; height: 150px;
  opacity: 1;
}
.hover-glow-expand:hover { border-color: #3AB54A; }
```

</details>

<details><summary><b>Border Glow</b> — <code>.hover-border-glow</code></summary>


*Add `.hover-border-glow` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-border-glow">Glow</div>
```


```css
.hover-border-glow {
  width: 90px; height: 90px;
  background: #161b22;
  border: 2px solid #30363d;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; color: #8b949e;
  transition: all 0.4s; cursor: pointer;
}
.hover-border-glow:hover {
  border-color: #3AB54A;
  box-shadow: 0 0 15px rgba(58,181,74,0.4), 0 0 30px rgba(58,181,74,0.2);
  animation: borderGlowPulse 1.5s ease-in-out infinite;
}
@keyframes borderGlowPulse {
  0%, 100% { box-shadow: 0 0 15px rgba(58,181,74,0.4), 0 0 30px rgba(58,181,74,0.2); }
  50% { box-shadow: 0 0 25px rgba(58,181,74,0.4), 0 0 50px rgba(58,181,74,0.3); }
}
```

</details>

<details><summary><b>Shadow Lift</b> — <code>.hover-shadow-lift</code></summary>


*Add `.hover-shadow-lift` to a card/link/image. Provides hover feedback on desktop — keep content usable without hover on touch.*


```html
<div class="fx-hover-shadow-lift">Lift</div>
```


```css
.hover-shadow-lift {
  width: 90px; height: 90px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; color: #8b949e;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
}
.hover-shadow-lift:hover {
  transform: translateY(-12px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.5), 0 0 0 1px #3AB54A;
}
```

</details>


### Borders & Dividers  ·  11 components

_Animated/gradient borders, glowing outlines, section dividers. Draw the eye to a featured card or premium tier._

**Pairs well with:** featured pricing card, highlighted cards, section breaks

<details><summary><b>Animated Gradient Border</b> — <code>.border-grad</code></summary>


*Apply `.border-grad` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-grad" style="position:relative"><span style="position:relative;z-index:1;color:var(--text-dim);font-size:0.75rem">Gradient</span></div>
```


```css
@property --angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}
.border-grad {
  position: relative;
  padding: 2px;
  border-radius: 10px;
}
.border-grad::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 10px;
  padding: 2px;
  background: conic-gradient(from var(--angle), #3AB54A, #2dd4bf, #f97316, #3AB54A);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  animation: gradBorderRotate 3s linear infinite;
}
@keyframes gradBorderRotate { to { --angle: 360deg; } }
```

</details>

<details><summary><b>Dashed Rotate</b> — <code>.border-dashed</code></summary>


*Apply `.border-dashed` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-dashed"><span style="font-size:0.75rem">Dashed</span></div>
```


```css
.border-dashed {
  border: 3px dashed #3AB54A;
  border-radius: 10px;
  background-image: repeating-linear-gradient(
    45deg, transparent, transparent 10px,
    rgba(58,181,74,0.15) 10px, rgba(58,181,74,0.15) 20px
  );
  background-color: #161b22;
}
```

</details>

<details><summary><b>Double Line Glow</b> — <code>.border-double-glow</code></summary>


*Apply `.border-double-glow` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-double-glow"><span style="font-size:0.75rem;color:var(--text-dim)">Double</span></div>
```


```css
.border-double-glow {
  border: 2px solid #3AB54A;
  outline: 2px solid #3AB54A;
  outline-offset: 4px;
  border-radius: 10px;
  background: #161b22;
  box-shadow: 0 0 15px rgba(58,181,74,0.4);
}
```

</details>

<details><summary><b>Corner Accent</b> — <code>.border-corner</code></summary>


*Apply `.border-corner` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-corner"><span style="font-size:0.75rem;color:var(--text-dim)">Corners</span></div>
```


```css
.border-corner {
  position: relative;
  border: 1px solid #30363d;
  border-radius: 10px;
  background: #161b22;
}
.border-corner::before, .border-corner::after {
  content: '';
  position: absolute;
  width: 24px; height: 24px;
  border-color: #3AB54A;
  border-style: solid;
}
.border-corner::before {
  top: -1px; left: -1px;
  border-width: 3px 0 0 3px;
  border-radius: 10px 0 0 0;
}
.border-corner::after {
  bottom: -1px; right: -1px;
  border-width: 0 3px 3px 0;
  border-radius: 0 0 10px 0;
}
```

</details>

<details><summary><b>Neon Pulse Border</b> — <code>.border-neon-pulse</code></summary>


*Apply `.border-neon-pulse` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-neon-pulse"><span style="font-size:0.75rem;color:var(--text-dim)">Pulse</span></div>
```


```css
.border-neon-pulse {
  border: 2px solid #3AB54A;
  border-radius: 10px;
  background: #161b22;
  animation: neonPulse 2s ease-in-out infinite;
}
@keyframes neonPulse {
  0%, 100% {
    box-shadow: 0 0 5px rgba(58,181,74,0.4), 0 0 10px rgba(58,181,74,0.4);
  }
  50% {
    box-shadow: 0 0 15px rgba(58,181,74,0.4), 0 0 30px rgba(58,181,74,0.4), 0 0 45px rgba(58,181,74,0.2);
  }
}
```

</details>

<details><summary><b>Gradient Rotate Border</b> — <code>.border-grad-rotate</code></summary>


*Apply `.border-grad-rotate` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-grad-rotate" style="position:relative"><div class="fx-border-grad-rotate-inner"><span style="font-size:0.75rem;color:var(--text-dim)">Spin</span></div></div>
```


```css
.border-grad-rotate {
  position: relative;
  padding: 3px;
  border-radius: 10px;
  overflow: hidden;
}
.border-grad-rotate::before {
  content: '';
  position: absolute;
  inset: -50%;
  background: conic-gradient(from 0deg, #3AB54A, #2dd4bf, #f97316, #ec4899, #3AB54A);
  animation: gradSpin 4s linear infinite;
}
.border-grad-rotate-inner {
  position: relative;
  z-index: 1;
  background: #161b22;
  border-radius: 8px;
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}
@keyframes gradSpin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Dotted Trail Border</b> — <code>.border-dotted-trail</code></summary>


*Apply `.border-dotted-trail` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-dotted-trail"><span style="font-size:0.75rem;color:var(--text-dim);position:relative;z-index:1">Trail</span></div>
```


```css
.border-dotted-trail {
  border: 2px dotted #30363d;
  border-radius: 10px;
  background: #161b22;
  position: relative;
  overflow: hidden;
}
.border-dotted-trail::after {
  content: '';
  position: absolute;
  top: -2px; left: -2px; right: -2px; bottom: -2px;
  border-radius: 10px;
  border: 2px dashed #3AB54A;
  animation: trailDash 6s linear infinite;
}
@keyframes trailDash { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Split Border</b> — <code>.border-split</code></summary>


*Apply `.border-split` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-split"><span style="font-size:0.75rem;color:var(--text-dim)">Split</span></div>
```


```css
.border-split {
  border: 1px solid #30363d;
  border-radius: 10px;
  background: #161b22;
  position: relative;
  transition: all 0.4s;
}
.border-split::before, .border-split::after {
  content: '';
  position: absolute;
  width: 20px; height: 20px;
  border-color: #3AB54A;
  border-style: solid;
  transition: all 0.4s;
  opacity: 0;
}
.border-split::before { top: -1px; left: -1px; border-width: 3px 0 0 3px; }
.border-split::after { bottom: -1px; right: -1px; border-width: 0 3px 3px 0; }
.border-split:hover::before,
.border-split:hover::after { opacity: 1; }
.border-split:hover { border-color: #3AB54A; }
```

</details>

<details><summary><b>Arrow Border</b> — <code>.border-arrow</code></summary>


*Apply `.border-arrow` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-arrow"><span style="font-size:0.75rem;color:var(--text-dim)">Arrows</span></div>
```


```css
.border-arrow {
  border: 2px solid #3AB54A;
  border-radius: 10px;
  background: #161b22;
  position: relative;
}
.border-arrow::before, .border-arrow::after {
  content: '';
  position: absolute;
  width: 0; height: 0;
}
.border-arrow::before { top: -8px; left: -8px; border-left: 10px solid #3AB54A; border-bottom: 10px solid transparent; }
.border-arrow::after { bottom: -8px; right: -8px; border-right: 10px solid #3AB54A; border-top: 10px solid transparent; }
```

</details>

<details><summary><b>Double Animated Border</b> — <code>.border-double-anim</code></summary>


*Apply `.border-double-anim` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-double-anim" style="position:relative"><div class="fx-border-double-anim-inner"><span style="font-size:0.75rem;color:var(--text-dim)">Dual</span></div></div>
```


```css
.border-double-anim {
  position: relative;
  padding: 4px;
  border-radius: 10px;
  background: conic-gradient(from 0deg, #3AB54A, transparent, #3AB54A);
  animation: gradSpin 3s linear infinite;
}
.border-double-anim::before {
  content: '';
  position: absolute;
  inset: 4px;
  border-radius: 8px;
  padding: 3px;
  background: conic-gradient(from 180deg, #2dd4bf, transparent, #2dd4bf);
  animation: gradSpin 3s linear infinite reverse;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}
.border-double-anim-inner {
  position: relative;
  z-index: 1;
  background: #161b22;
  border-radius: 5px;
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}
@keyframes gradSpin { to { transform: rotate(360deg); } }
```

</details>

<details><summary><b>Box Shadow Border</b> — <code>.border-shadow</code></summary>


*Apply `.border-shadow` to a container to draw attention (e.g. the featured pricing tier).*


```html
<div class="fx-border-item fx-border-shadow"><span style="font-size:0.75rem;color:var(--text-dim)">Shadow</span></div>
```


```css
.border-shadow {
  border: none;
  border-radius: 10px;
  background: #161b22;
  animation: shadowBorder 3s ease-in-out infinite;
}
@keyframes shadowBorder {
  0%, 100% {
    box-shadow: 6px 0 0 -1px #3AB54A, -6px 0 0 -1px #3AB54A,
      0 6px 0 -1px #3AB54A, 0 -6px 0 -1px #3AB54A;
  }
  25% {
    box-shadow: 8px 2px 0 -1px #2dd4bf, -8px -2px 0 -1px #2dd4bf,
      2px 8px 0 -1px #2dd4bf, -2px -8px 0 -1px #2dd4bf;
  }
  50% {
    box-shadow: 4px 4px 0 -1px #f97316, -4px -4px 0 -1px #f97316,
      4px -4px 0 -1px #f97316, -4px 4px 0 -1px #f97316;
  }
  75% {
    box-shadow: 6px -2px 0 -1px #ec4899, -6px 2px 0 -1px #ec4899,
      -2px 6px 0 -1px #ec4899, 2px -6px 0 -1px #ec4899;
  }
}
```

</details>


### Misc & Effects  ·  9 components

_Specialty effects — badges, tooltips, scroll cues, decorative accents. Spice, not the meal._

**Pairs well with:** badges on cards, tooltips, scroll indicators

<details><summary><b>Tooltip</b> — <code>.tooltip-wrap</code></summary>


*Apply `.tooltip-wrap` as a decorative accent. Use sparingly.*


```html
<div class="fx-tooltip-wrap"><div class="fx-tooltip-box">Hello!</div><div class="fx-tooltip-trigger">Hover me</div></div>
```


```css
.tooltip-wrap { position: relative; display: inline-flex; }
.tooltip-trigger {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e2e8f0;
  padding: 8px 16px;
  cursor: pointer;
}
.tooltip-box {
  position: absolute;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%) translateY(5px);
  background: #e2e8f0;
  color: #0d1117;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: all 0.2s;
}
.tooltip-box::after {
  content: '';
  position: absolute;
  top: 100%; left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: #e2e8f0;
}
.tooltip-wrap:hover .tooltip-box {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
```

</details>

<details><summary><b>Accordion</b> — <code>.accordion</code></summary>


*Apply `.accordion` as a decorative accent. Use sparingly.*


```html
<div class="fx-accordion"><div class="fx-accordion-header" onclick="toggleAccordion(this)"><span>Click me</span><span class="fx-accordion-arrow">▼</span></div><div class="fx-accordion-body">Hidden content revealed!</div></div>
```


```css
.accordion {
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
}
.accordion-header {
  padding: 10px 12px;
  background: #161b22;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
}
.accordion-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s, padding 0.3s;
  padding: 0 12px;
  font-size: 0.8rem;
  color: #8b949e;
}
.accordion-header.open + .accordion-body {
  max-height: 100px;
  padding: 10px 12px;
}
```

</details>

<details><summary><b>Checkbox Custom</b> — <code>.checkbox-wrap</code></summary>


*Apply `.checkbox-wrap` as a decorative accent. Use sparingly.*


```html
<label class="fx-checkbox-wrap"><input type="checkbox"><span class="fx-checkbox-box"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg></span><span>Check me</span></label>
```


```css
.checkbox-wrap {
  display: flex; align-items: center; gap: 10px;
  cursor: pointer;
}
.checkbox-wrap input { display: none; }
.checkbox-box {
  width: 22px; height: 22px;
  border: 2px solid #30363d;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.checkbox-box svg {
  width: 14px; height: 14px;
  stroke: #000; stroke-width: 3; fill: none;
  opacity: 0; transform: scale(0);
  transition: all 0.2s;
}
.checkbox-wrap input:checked + .checkbox-box {
  background: #3AB54A;
  border-color: #3AB54A;
}
.checkbox-wrap input:checked + .checkbox-box svg {
  opacity: 1; transform: scale(1);
}
```

</details>

<details><summary><b>Radio Custom</b> — <code>.radio-wrap</code></summary>


*Apply `.radio-wrap` as a decorative accent. Use sparingly.*


```html
<label class="fx-radio-wrap"><input type="radio" name="demo-radio"><span class="fx-radio-circle"><span class="fx-radio-dot"></span></span><span>Option A</span></label>
```


```css
.radio-wrap {
  display: flex; align-items: center; gap: 10px;
  cursor: pointer;
}
.radio-wrap input { display: none; }
.radio-circle {
  width: 22px; height: 22px;
  border: 2px solid #30363d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.radio-dot {
  width: 10px; height: 10px;
  background: #000;
  border-radius: 50%;
  opacity: 0; transform: scale(0);
  transition: all 0.2s;
}
.radio-wrap input:checked + .radio-circle {
  border-color: #3AB54A;
  background: #3AB54A;
}
.radio-wrap input:checked + .radio-circle .radio-dot {
  opacity: 1; transform: scale(1);
}
```

</details>

<details><summary><b>Toggle Switch</b> — <code>.toggle-wrap</code></summary>


*Apply `.toggle-wrap` as a decorative accent. Use sparingly.*


```html
<label class="fx-toggle-wrap"><input type="checkbox"><span class="fx-toggle-track"><span class="fx-toggle-thumb"></span></span><span>Toggle</span></label>
```


```css
.toggle-wrap {
  display: flex; align-items: center; gap: 10px;
  cursor: pointer;
}
.toggle-wrap input { display: none; }
.toggle-track {
  width: 44px; height: 24px;
  background: #30363d;
  border-radius: 12px;
  position: relative;
  transition: background 0.3s;
}
.toggle-thumb {
  position: absolute;
  top: 2px; left: 2px;
  width: 20px; height: 20px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.3s;
}
.toggle-wrap input:checked + .toggle-track {
  background: #3AB54A;
}
.toggle-wrap input:checked + .toggle-track .toggle-thumb {
  transform: translateX(20px);
}
```

</details>

<details><summary><b>Progress Bar</b> — <code>.progress-bar</code></summary>


*Apply `.progress-bar` as a decorative accent. Use sparingly.*


```html
<div class="fx-progress-wrap"><div class="fx-progress-label"><span>Progress</span><span>72%</span></div><div class="fx-progress-bar"><div class="fx-progress-fill"></div></div></div>
```


```css
.progress-bar {
  width: 100%; height: 8px;
  background: #30363d;
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3AB54A, #2dd4bf);
  border-radius: 4px;
  width: 72%;
}
```

</details>

<details><summary><b>Badge</b> — <code>.badge</code></summary>


*Apply `.badge` as a decorative accent. Use sparingly.*


```html
<div style="display:flex;gap:8px"><span class="fx-badge fx-badge-green">Active</span><span class="fx-badge fx-badge-orange">Pending</span><span class="fx-badge fx-badge-blue">New</span></div>
```


```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.badge-green { background: rgba(58,181,74,0.15); color: #3AB54A; border: 1px solid rgba(58,181,74,0.3); }
.badge-orange { background: rgba(249,115,22,0.15); color: #f97316; border: 1px solid rgba(249,115,22,0.3); }
.badge-blue { background: rgba(59,130,246,0.15); color: #3b82f6; border: 1px solid rgba(59,130,246,0.3); }
```

</details>

<details><summary><b>Skeleton Loader</b> — <code>.skeleton</code></summary>


*Apply `.skeleton` as a decorative accent. Use sparingly.*


```html
<div class="fx-skeleton"><div class="fx-skeleton-line"></div><div class="fx-skeleton-line"></div><div class="fx-skeleton-line"></div></div>
```


```css
.skeleton { display: flex; flex-direction: column; gap: 10px; width: 130px; }
.skeleton-line {
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(90deg, #30363d 25%, #21262d 50%, #30363d 75%);
  background-size: 200% 100%;
  animation: skeletonShimmer 1.5s ease infinite;
}
.skeleton-line:nth-child(1) { width: 80%; }
.skeleton-line:nth-child(2) { width: 100%; }
.skeleton-line:nth-child(3) { width: 60%; }
@keyframes skeletonShimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

</details>

<details><summary><b>Breadcrumb</b> — <code>.breadcrumb</code></summary>


*Apply `.breadcrumb` as a decorative accent. Use sparingly.*


```html
<div class="fx-breadcrumb"><a href="#">Home</a><span class="fx-bc-sep">/</span><a href="#">Products</a><span class="fx-bc-sep">/</span><span class="fx-bc-current">Detail</span></div>
```


```css
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}
.breadcrumb a {
  color: #8b949e;
  text-decoration: none;
  transition: color 0.2s;
  position: relative;
}
.breadcrumb a:hover { color: #3AB54A; }
.breadcrumb a::after {
  content: '';
  position: absolute;
  bottom: -2px; left: 0;
  width: 0; height: 1px;
  background: #3AB54A;
  transition: width 0.3s;
}
.breadcrumb a:hover::after { width: 100%; }
.breadcrumb .bc-sep { color: #8b949e; opacity: 0.5; }
.breadcrumb .bc-current { color: #3AB54A; font-weight: 600; }
```

</details>

