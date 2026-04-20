(function() {
  // Prevent the script from running multiple times
  if (window.__SCRAPER_BUILDER_INITIALIZED__) return;
  window.__SCRAPER_BUILDER_INITIALIZED__ = true;

  console.log('Scraper Builder Overlay Initialized');

  let hoveredElement = null;
  let isTaggingMode = true;
  const highlightId = 'scraper-builder-highlight';

  // Create highlight element
  const highlight = document.createElement('div');
  highlight.id = highlightId;
  highlight.style.position = 'absolute';
  highlight.style.pointerEvents = 'none';
  highlight.style.border = '2px solid #3b82f6';
  highlight.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
  highlight.style.zIndex = '999999';
  highlight.style.display = 'none';
  highlight.style.transition = 'all 0.1s ease-out';
  document.body.appendChild(highlight);

  // Listen for messages from parent
  window.addEventListener('message', (event) => {
    if (event.data.type === 'SET_TAGGING_MODE') {
      isTaggingMode = event.data.enabled;
      if (!isTaggingMode) {
        highlight.style.display = 'none';
      }
    }
  });

  // Tell parent we're ready
  window.parent.postMessage({ type: 'OVERLAY_READY' }, '*');

  function getSelector(el) {
    // 1. Try common test attributes
    const testAttrs = ['data-test', 'data-testid', 'data-qa', 'data-cy'];
    for (const attr of testAttrs) {
      const val = el.getAttribute(attr);
      if (val) return `[${attr}="${val}"]`;
    }

    // 2. Try ID (if it looks stable/not auto-generated)
    if (el.id && !/^\d|[\d-]{5,}/.test(el.id)) {
      return `#${el.id}`;
    }

    // 3. Try unique classes
    if (el.classList.length > 0) {
      for (const className of Array.from(el.classList)) {
        // Skip common utility or dynamic classes
        if (['active', 'selected', 'hover', 'hidden'].includes(className)) continue;
        
        const selector = `.${className}`;
        try {
          if (document.querySelectorAll(selector).length === 1) {
            return selector;
          }
        } catch (e) {}
      }
    }

    // 4. Fallback to positional path
    if (el === document.body) return 'body';
    
    let path = [];
    let current = el;
    while (current && current !== document.documentElement) {
      let selector = current.tagName.toLowerCase();
      
      // Add nth-of-type if there are siblings
      if (current.parentElement) {
        let siblings = Array.from(current.parentElement.children).filter(s => s.tagName === current.tagName);
        if (siblings.length > 1) {
          let index = siblings.indexOf(current) + 1;
          selector += `:nth-of-type(${index})`;
        }
      }
      
      path.unshift(selector);
      current = current.parentElement;
    }
    return path.join(' > ');
  }

  document.addEventListener('mouseover', (e) => {
    if (!isTaggingMode) return;
    
    const el = e.target;
    if (el === highlight || el.id === highlightId) return;

    hoveredElement = el;
    const rect = el.getBoundingClientRect();
    
    highlight.style.width = `${rect.width}px`;
    highlight.style.height = `${rect.height}px`;
    highlight.style.top = `${rect.top + window.scrollY}px`;
    highlight.style.left = `${rect.left + window.scrollX}px`;
    highlight.style.display = 'block';
  });

  document.addEventListener('click', (e) => {
    // If it's a link click, always intercept to handle proxy navigation
    const link = e.target.closest('a');
    if (link && link.href) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log('Link clicked, navigating within proxy:', link.href);
      
      window.parent.postMessage({
        type: 'NAVIGATE',
        url: link.href
      }, '*');
      return;
    }

    if (!isTaggingMode) return;

    e.preventDefault();
    e.stopPropagation();

    if (hoveredElement) {
      const selector = getSelector(hoveredElement);
      const text = hoveredElement.innerText.trim();
      
      console.log('Element selected:', selector);
      
      window.parent.postMessage({
        type: 'ELEMENT_SELECTED',
        selector: selector,
        text: text.substring(0, 100) // Preview text
      }, '*');
    }
  }, true);

  // Clean up on window unload
  window.addEventListener('unload', () => {
    if (highlight.parentElement) {
      document.body.removeChild(highlight);
    }
  });
})();
