var hashCode = (string) => {
    var hash = 0, i, chr;
    if (string.length === 0) return hash;
    for (i = 0; i < string.length; i++) {
        chr = string.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
}

var getXPathForElement = (element) => {
    const getElementIndex = (element) => {
        let index = 1;
        let sibling = element.previousElementSibling;
        
        while (sibling) {
            if (sibling.localName === element.localName) {
                index++;
            }
            sibling = sibling.previousElementSibling;
        }
        
        return index;
    };

    const segs = elm => {
        if (!elm || elm.nodeType !== 1) return [''];
        if (elm.id && document.getElementById(elm.id) === elm) return [`id("${elm.id}")`];
        const localName = typeof elm.localName === 'string' ? elm.localName.toLowerCase() : 'unknown';
        let index = getElementIndex(elm);
        
        return [...segs(elm.parentNode), `${localName}[${index}]`];
    };
    return segs(element).join('/');
}

// Create a Map to store used hashes and their counters
const usedHashes = new Map();

document.querySelectorAll('*').forEach((element, index) => {
    try {
        
        const xpath = getXPathForElement(element);
        const hash = hashCode(xpath);
        const baseId = hash.toString(36);

        const markHidden = (hidden_element) => {
            // Mark the hidden element itself
            hidden_element.setAttribute('data-hidden', 'true');

        }
    
        // const is_marked_hidden = element.getAttribute("data-hidden") === "true";
        const isHidden = !element.checkVisibility();
                            // computedStyle.width === '0px' || 
                            // computedStyle.height === '0px';
    
        if (isHidden) {
            markHidden(element);
        }else{
            element.removeAttribute("data-hidden") // in case we hid it in a previous call
        }
        
        let uniqueId = baseId;
        let counter = 0;
        
        // Check if this hash has been used before
        while (usedHashes.has(uniqueId)) {
            // If it has, increment the counter and create a new uniqueId
            counter++;
            uniqueId = `${baseId}_${counter}`;
        }
        
        // Add the uniqueId to the usedHashes Map
        usedHashes.set(uniqueId, true);
        element.setAttribute('d-id', uniqueId);
    } catch (error) {
        // Fallback: use a hash of the tag name and index
        const fallbackId = hashCode(`${element.tagName}_${index}`).toString(36);
        console.error('Error processing element, using fallback:',fallbackId, element, error);

        element.setAttribute('d-id', `fallback_${fallbackId}`);
    }
});