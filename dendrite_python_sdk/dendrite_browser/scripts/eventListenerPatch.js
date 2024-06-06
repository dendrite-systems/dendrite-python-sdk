EventTarget.prototype._getEventListeners = function(eventType) {
    if (!this.eventListenerList) {
        this.eventListenerList = {};
    }

    ['click', 'dblclick', 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'keydown', 'keyup', 'keypress'].forEach(type => {
        if (!eventType || eventType === type) {
            if (this[`on${type}`]) {
                if (!this.eventListenerList[type]) {
                    this.eventListenerList[type] = [];
                }
                this.eventListenerList[type].push({ listener: this[`on${type}`], inline: true });
            }
        }
    });

    if (eventType === undefined) {
        return this.eventListenerList;
    }
    return this.eventListenerList[eventType];
};

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

EventTarget.prototype._removeEventListener = EventTarget.prototype.removeEventListener;
EventTarget.prototype._addEventListener = EventTarget.prototype.addEventListener;

EventTarget.prototype.addEventListener = function(event, listener, options = false) {
    this._addEventListener(event, listener, options);
    

    if (!this.eventListenerList) {
        this.eventListenerList = {};
    }
    if (!this.eventListenerList[event]) {
        this.eventListenerList[event] = [];
    }
    this.eventListenerList[event].push({ listener, options, outerHTML: this.outerHTML });
};

EventTarget.prototype.removeEventListener = function(event, listener, options = false, suppress = false) {
    if (!suppress) {
        this._removeEventListener(event, listener, options);
    }

    if (this.eventListenerList && this.eventListenerList[event]) {
        for (let i = 0; i < this.eventListenerList[event].length; ++i) {
            if (this.eventListenerList[event][i].listener === listener && this.eventListenerList[event][i].options === options) {
                this.eventListenerList[event].splice(i, 1);
                break;
            }
        }
        if (this.eventListenerList[event].length === 0) {
            delete this.eventListenerList[event];
        }
    }
};

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

Object.defineProperties(EventTarget.prototype, {
    on: { enumerable: false },
    off: { enumerable: false },
    emit: { enumerable: false }
});