boxee.showNotification("BOOM", ".", 1);

var started = false;
var intendedToPlay = true;

var fullscreenSet = false;

function start() {
    var result = browser.execute("document.getElementsByTagName(\"object\")[0].setIsPlaying(1);");
    boxee.showNotification("START: " + result, ".", 1);
}

function play() {
    intendedToPlay = true;
    start();
}

function pause() {
    intendedToPlay = false;
    var result = browser.execute("document.getElementsByTagName(\"object\")[0].setIsPlaying(0);");
    boxee.showNotification("PAUSE: " + result, ".", 1);
}

function isPlaying() {
    var result = browser.execute("document.getElementsByTagName(\"object\")[0].getIsPlaying();");
    boxee.showNotification("IS_PLAYING: " + result, ".", 1);
    return  result === "true";
}

function isPaused() {
    return !isPlaying();
}

function hasStarted() {
    var result = started || isPlaying();
    boxee.showNotification("HAS_STARTED: " + result, ".", 1);
    return result;
}

function hasStartedPoll() {
    if (hasStarted()) {
        started = true;
        return;
    }

    setTimeout(hasStartedPoll, 5000);
}

function hasEnded() {
    return started && intendedToPlay && isPaused();
}

function hasEndedPoll() {
    if (hasEnded()) {
        boxee.notifyPlaybackEnded();
    } else {
        setTimeout(hasEndedPoll, 5000);
    }
}

function isLive() {
    return false;
}

function seekTo(i) {
}

function time() {
}

function duration() {
}

function updateState() {
    playerState.canSeek = false;
    playerState.canSeekTo = false;
    playerState.canPause = true;
    playerState.isPaused = isPaused();
    playerState.canSetFullScreen = false;
    playerState.time = 0;
    playerState.duration = 0;
    playerState.progress = 0;
}

function isFullScreen() {
    boxee.showNotification("IS_FULLSCREEN: " + fullscreenSet, ".", 1);
    return fullscreenSet;
}

function setFullScreen() {
    if (!isFullScreen()) {
        setTimeout(setFullScreen, 10000);
    }
    for (var w1 in boxee.getWidgets()) {
        var widg = boxee.getWidgets()[w1];
        boxee.showNotification("WIDGET id: " + widg.getAttribute("id"), ".", 1);
        if (/[0-9]*/.test(widg.getAttribute("id"))) {
            fullscreenSet = true;
            widg.setActive();
        }
    }
}

boxee.onDocumentLoading = function () {
    boxee.setMode(boxee.PLAYER_MODE);
    boxee.realFullScreen = true;
    setFullScreen();
    hasStartedPoll();
    //setTimeout(hasEndedPoll, 1000);
    //boxee.showNotification("DocLoading_Done", ".", 1);
};

boxee.onDocumentLoaded = function () {
    //hasStartedPoll();
};

boxee.onPlay = play;

boxee.onPause = pause;

boxee.onSeekTo = function (millis) {
    seekTo(millis / 1000);
};

boxee.onSkip = function () {
    seekTo(time() + 10);
};

boxee.onBigSkip = function () {
    seekTo(time() + 30);
};

boxee.onBack = function () {
    seekTo(time() - 10);
};

boxee.onBigBack = function () {
    seekTo(time() - 30);
};

boxee.onSetFullScreen = setFullScreen;

boxee.onUpdateState = updateState;

