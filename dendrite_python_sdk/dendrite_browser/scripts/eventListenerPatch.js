// Save the original methods before redefining them
EventTarget.prototype._originalAddEventListener = EventTarget.prototype.addEventListener;
EventTarget.prototype._originalRemoveEventListener = EventTarget.prototype.removeEventListener;

// Redefine the addEventListener method
EventTarget.prototype.addEventListener = function(event, listener, options = false) {
    // Initialize the eventListenerList if it doesn't exist
    if (!this.eventListenerList) {
        this.eventListenerList = {};
    }
    // Initialize the event list for the specific event if it doesn't exist
    if (!this.eventListenerList[event]) {
        this.eventListenerList[event] = [];
    }
    // Add the event listener details to the event list
    this.eventListenerList[event].push({ listener, options, outerHTML: this.outerHTML });

    // Call the original addEventListener method
    this._originalAddEventListener(event, listener, options);
};

// Redefine the removeEventListener method
EventTarget.prototype.removeEventListener = function(event, listener, options = false) {
    // Remove the event listener details from the event list
    if (this.eventListenerList && this.eventListenerList[event]) {
        this.eventListenerList[event] = this.eventListenerList[event].filter(
            item => item.listener !== listener
        );
    }

    // Call the original removeEventListener method
    this._originalRemoveEventListener( event, listener, options);
};

// Get event listeners for a specific event type or all events if not specified
EventTarget.prototype._getEventListeners = function(eventType) {
    if (!this.eventListenerList) {
        this.eventListenerList = {};
    }

    const eventsToCheck = ['click', 'dblclick', 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'keydown', 'keyup', 'keypress'];

    eventsToCheck.forEach(type => {
        if (!eventType || eventType === type) {
            if (this[`on${type}`]) {
                if (!this.eventListenerList[type]) {
                    this.eventListenerList[type] = [];
                }
                this.eventListenerList[type].push({ listener: this[`on${type}`], inline: true });
            }
        }
    });

    return eventType === undefined ? this.eventListenerList : this.eventListenerList[eventType];
};

// Utility to show events
function _showEvents(events) {
    let result = '';
    for (let event in events) {
        result += `${event} ----------------> ${events[event].length}\n`;
        for (let listenerObj of events[event]) {
            result += `${listenerObj.listener.toString()}\n`;
        }
    }
    return result;
}

// Extend EventTarget prototype with utility methods
EventTarget.prototype.on = function(event, callback, options) {
    this.addEventListener(event, callback, options);
    return this;
};

EventTarget.prototype.off = function(event, callback, options) {
    this.removeEventListener(event, callback, options);
    return this;
};

EventTarget.prototype.emit = function(event, args = null) {
    this.dispatchEvent(new CustomEvent(event, { detail: args }));
    return this;
};

// Make these methods non-enumerable
Object.defineProperties(EventTarget.prototype, {
    on: { enumerable: false },
    off: { enumerable: false },
    emit: { enumerable: false }
});
