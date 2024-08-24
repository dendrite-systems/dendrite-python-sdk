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
    const idx = (sib, name) => sib
        ? idx(sib.previousElementSibling, name||sib.localName) + (sib.localName == name)
        : 1;
    const segs = elm => !elm || elm.nodeType !== 1
        ? ['']
        : elm.id && document.getElementById(elm.id) === elm
            ? [`id("${elm.id}")`]
            : [...segs(elm.parentNode), `${elm.localName.toLowerCase()}[${idx(elm)}]`];
    return segs(element).join('/');
}

var traverseAndSetAttribute = (root) => {
    if (root.nodeType === Node.ELEMENT_NODE) {
        const xpath = getXPathForElement(root);
        const uniqueId = hashCode(xpath).toString(36);
        root.setAttribute('d-id', uniqueId);

        // Check if the element has a shadow root
        if (root.shadowRoot) {
            traverseAndSetAttribute(root.shadowRoot);
        }
    }

    // Traverse child nodes
    root.childNodes.forEach(child => {
        traverseAndSetAttribute(child);
    });
}

// Start traversal from the document body
traverseAndSetAttribute(document.body);

// Handle any shadow roots in the main document
document.querySelectorAll('*').forEach(element => {
    if (element.shadowRoot) {
        traverseAndSetAttribute(element.shadowRoot);
    }
});

console.log(document)