# Animation recipes: the GSAP behind the graphics

All compositions share: `const tl = gsap.timeline({paused:true})`, times in seconds relative
to the element's `t0` in the short, a final `tl.to({}, {duration:.1}, DUR-0.1)` so the timeline
spans the full `data-duration`, and `window.__timelines['<id>'] = tl`.

Take the word sheet (`python3 scripts/words.py work/words.json --sheet`) and put every tween on a word.

## Card entrance (every card)

```js
tl.fromTo('#c', {opacity:0, y:30, scale:.96}, {opacity:1, y:0, scale:1, duration:.45, ease:'power3.out'}, 0);
```
Slide-in from the side for a pair: `{x:-30}` for the left card, `{x:30}` for the right, 0.35s apart.

## Words one by one (title)

```html
<span class="wd">How</span><span class="wd">open</span>…   /* .wd{display:inline-block;opacity:0} */
```
```js
tl.fromTo('.wd', {opacity:0, y:26}, {opacity:1, y:0, duration:.4, stagger:.08, ease:'power3.out'}, .25);
tl.to('#ul', {width:860, duration:1.4, ease:'power2.out'}, .6);   // accent bar along the top edge
```

## Pills on an enumeration (reader / post)

```js
const P=document.querySelectorAll('.pill'); const T=[5.85,6.6,7.35,8.05,8.7];   // = her words
P.forEach((p,i)=>tl.fromTo(p,{opacity:0,y:14,scale:.9},{opacity:1,y:0,scale:1,duration:.35,ease:'back.out(1.6)'},T[i]));
```
Put each time ~0.05s before the word's start so the pill is fully on when she lands on it.

## Marching dashed line, arrow or ring (the accent that keeps a still card alive)

```html
<svg width="160" height="80" viewBox="0 0 160 80">
  <path class="dash" d="M30 40 H130"/>                       <!-- .dash{stroke:var(--brand);stroke-width:6;fill:none;stroke-dasharray:16 12;stroke-linecap:round} -->
  <polygon class="ah" points="152,40 126,26 126,54"/>        <!-- .ah{fill:var(--brand)} -->
</svg>
<svg viewBox="0 0 660 88" width="660" height="88"><rect class="dash" x="4" y="4" width="652" height="80" rx="24"/></svg>  <!-- ring -->
```
```js
// K cycles of 0.6s until the end of the comp. NEVER repeat:-1 (renderer refuses).
const K=Math.floor((DUR-start)/0.6);
tl.to('#arr', {opacity:1, duration:.3}, start);
tl.to('#arr .dash', {strokeDashoffset:-28*K, duration:.6*K, ease:'none'}, start);
```
Direction: negative offset marches toward the arrowhead drawn at the path's end; use `+28*K`
for a path drawn the other way (the right-hand arrow in `match`).

## Bar that fills (feed)

```js
tl.to('#seg1', {width:213, duration:1.1, ease:'power2.out'}, 1.3);   // a third of 640
tl.to('#l1',  {opacity:1, duration:.35}, 2.3);
tl.to('#seg2', {width:427, duration:1.0, ease:'power2.out'}, 5.5);   // "the rest"
```

## Badge pop + result (match)

```js
tl.fromTo('#badge', {opacity:0, scale:.6}, {opacity:1, scale:1, duration:.45, ease:'back.out(2)'}, 5.65);
tl.fromTo('#res',   {opacity:0, y:14},     {opacity:1, y:0,   duration:.4,  ease:'power3.out'},  7.05);
```

## State flip that survives seeking (match → no match)

Two elements at the same position, crossfade. No callbacks, no `textContent` sets.
```js
tl.to('#badge', {opacity:0, duration:.3}, 8.9); tl.to('#badge2', {opacity:1, duration:.3}, 8.9);
tl.to('#res',   {opacity:0, duration:.3}, 8.95); tl.to('#res2',  {opacity:1, duration:.3}, 8.95);
tl.to('#ar1,#ar2,#ar3', {opacity:.35, duration:.4}, 9.0);   // arrows stay but go quiet
```

## Strike-through + tag (reader punchline)

```css
#say{color:var(--muted);text-decoration:line-through;opacity:0}
#tag{background:var(--brand);color:#fff;border-radius:999px;padding:12px 22px;font-weight:800;opacity:0}
```
```js
tl.to('#say', {opacity:1, duration:.35}, 12.4);
tl.to('#ring', {opacity:1, duration:.3}, 15.9);  /* + marching dash on #ring .dash */
tl.fromTo('#tag', {opacity:0, x:-20}, {opacity:1, x:0, duration:.4, ease:'power3.out'}, 16.2);
```

## Cursor click (end screen)

```js
gsap.set('#cursor', {x:700, y:1000, autoAlpha:0});
tl.to('#cursor', {autoAlpha:1, duration:.2}, 1.5)
  .to('#cursor', {x:515, y:600, duration:.7, ease:'power2.inOut'}, 1.55)
  .to('#cursor', {scale:.82, duration:.1, yoyo:true, repeat:1, transformOrigin:'20% 10%'}, 2.3)
  .fromTo('#play', {scale:1}, {scale:1.18, duration:.2, ease:'back.out(3)', yoyo:true, repeat:1}, 2.35);
```
Finite `repeat:1` is fine; only infinite repeats are refused.

## Fade in / out is NOT in the comp

`assemble.py` fades a movie element in over `fade` (default 0.3s) and out over the last 0.5s
before `t1`, and holds the last frame if the movie is shorter than its slot. End every comp on a
hold, not on its own fade.
