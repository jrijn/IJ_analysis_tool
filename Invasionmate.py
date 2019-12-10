from ij import IJ, WindowManager
from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking import LAPUtils
from ij import IJ
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import sys
import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer

# Get currently selected image
# imp = WindowManager.getCurrentImage()
imp = IJ.openImage('http://fiji.sc/samples/FakeTracks.tif')
imp.show()

# ----------------------------
# Create the model object now
# ----------------------------

# Some of the parameters we configure below need to have
# a reference to the model at creation. So we create an
# empty model now.

model = Model()

# Send all messages to ImageJ log window.
model.setLogger(Logger.IJ_LOGGER)

# ------------------------
# Prepare settings object
# ------------------------

settings = Settings()
settings.setFrom(imp)

# Configure detector - We use the Strings for the keys
settings.detectorFactory = LogDetectorFactory()
settings.detectorSettings = {
    'DO_SUBPIXEL_LOCALIZATION': True,
    'RADIUS': 2.5,
    'TARGET_CHANNEL': 1,
    'THRESHOLD': 0.,
    'DO_MEDIAN_FILTERING': False,
}

# Configure spot filters - Classical filter on quality
# filter1 = FeatureFilter('QUALITY', 30, True)
# settings.addSpotFilter(filter1)

# Configure tracker - We want to allow merges and fusions
settings.trackerFactory = SparseLAPTrackerFactory()
settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap()  # almost good enough
settings.trackerSettings['LINGKING_MAX_DISTANCE'] = 10.0
settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 10.0
settings.trackerSettings['MAX_FRAME_GAP'] = 240
settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
settings.trackerSettings['ALLOW_TRACK_MERGING'] = True

# Add the analyzers for some spot features.
# You need to configure TrackMate with analyzers that will generate
# the data you need.
# Here we just add two analyzers for spot, one that computes generic
# pixel intensity statistics (mean, max, etc...) and one that computes
# an estimate of each spot's SNR.
# The trick here is that the second one requires the first one to be in
# place. Be aware of this kind of gotchas, and read the docs.
settings.addSpotAnalyzerFactory(SpotIntensityAnalyzerFactory())
settings.addSpotAnalyzerFactory(SpotContrastAndSNRAnalyzerFactory())

# Configure track analyzers - Later on we want to filter out tracks
# based on their displacement, so we need to state that we want
# track displacement to be calculated. By default, out of the GUI,
# not features are calculated.

# The displacement feature is provided by the TrackDurationAnalyzer.

settings.addTrackAnalyzer(TrackDurationAnalyzer())

# Configure track filters - We want to get rid of the two immobile spots at
# the bottom right of the image. Track displacement must be above 10 pixels.

filter2 = FeatureFilter('TRACK_DISPLACEMENT', 10, True)
settings.addTrackFilter(filter2)

# -------------------
# Instantiate plugin
# -------------------

trackmate = TrackMate(model, settings)

# --------
# Process
# --------

ok = trackmate.checkInput()
if not ok:
    sys.exit(str(trackmate.getErrorMessage()))

ok = trackmate.process()
if not ok:
    sys.exit(str(trackmate.getErrorMessage()))

# ----------------
# Display results
# ----------------

model.getLogger().log('Found ' + str(model.getTrackModel().nTracks(True)) + ' tracks.')

selectionModel = SelectionModel(model)
displayer = HyperStackDisplayer(model, selectionModel, imp)
displayer.render()
displayer.refresh()

# Echo results with the log\ger we set at start:
# model.getLogger().log(str(model))

# The feature model, that stores edge and track features.
fm = model.getFeatureModel()

for id in model.getTrackModel().trackIDs(True):

    # Fetch the track feature from the feature model.
    v = fm.getTrackFeature(id, 'TRACK_MEAN_SPEED')
    model.getLogger().log('')
    model.getLogger().log(
        'Track ' + str(id) + ': mean velocity = ' + str(v) + ' ' + model.getSpaceUnits() + '/' + model.getTimeUnits())

    track = model.getTrackModel().trackSpots(id)
    for spot in track:
        sid = spot.ID()
        # Fetch spot features directly from spot.
        x = spot.getFeature('POSITION_X')
        y = spot.getFeature('POSITION_Y')
        t = spot.getFeature('FRAME')
        q = spot.getFeature('QUALITY')
        snr = spot.getFeature('SNR')
        mean = spot.getFeature('MEAN_INTENSITY')
        model.getLogger().log(
            '\tspot ID = ' + str(sid) + ': x=' + str(x) + ', y=' + str(y) + ', t=' + str(t) + ', q=' + str(
                q) + ', snr=' + str(snr) + ', mean = ' + str(mean))
