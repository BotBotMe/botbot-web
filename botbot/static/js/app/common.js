// usage: log('inside coolFunc',this,arguments);
// http://paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function () {
    log.history = log.history || [];   // store logs to an array for reference
    log.history.push(arguments);
    if (this.console) {
        console.log(Array.prototype.slice.call(arguments));
    }
};

// Prevent default hash jump in browsers
if (location.hash) {
    window.scrollTo(0, 0);
    setTimeout(function() {
        window.scrollTo(0, 0);
    }, 0);
}
