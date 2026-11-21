"""Human-reviewed EN dialogue direction, including translated epilogue scenes.

This changes performance metadata only; no scene timing or THN authoring.
Parenthetical acting notes in the existing EN text inform these selections.
"""

DIRECTION = {
    'Msn1Intro': {
        'WARM': [10, 20, 120, 150, 160], 'UNCERTAIN': [40], 'STERN': [50],
        'EXCITED': [70, 90, 100], 'SARDONIC': [80, 110], 'REFLECTIVE': [140],
    },
    'Msn1Cityscape': {'UNCERTAIN': [20], 'DRY': [30], 'WEARY': [40]},
    'Msn1Offer': {
        'WARM': [10, 20, 110], 'SARDONIC': [40], 'REASSURING': [50, 70],
        'UNCERTAIN': [90], 'AMUSED': [100],
    },
    'Msn1Berlin': {'WARM': [10, 20], 'SARDONIC': [30]},
    'Msn1Bizmark': {
        'WARM': [10, 20, 90, 150, 160], 'PROUD': [100], 'ANGRY': [120],
    },
    'Msn2Offer': {
        'WARM': [20], 'STERN': [40], 'SARDONIC': [50, 240], 'SOMBRE': [70, 80],
        'UNCERTAIN': [220], 'REASSURING': [230], 'AMUSED': [250],
    },
    'Msn2Miner': {
        'WARM': [10, 20], 'WEARY': [40, 45], 'PROUD': [60], 'UNCERTAIN': [80],
        'STERN': [70, 90], 'ANGRY': [100], 'SARDONIC': [110], 'CONCERNED': [120],
    },
    'Msn2Done': {
        'WARM': [10, 50], 'UNCERTAIN': [20], 'STERN': [30, 100],
        'AMUSED': [70], 'DETERMINED': [90, 110], 'PROUD': [130],
    },
    'Msn3Offer': {
        'WARM': [10, 20, 30], 'SARDONIC': [80, 130], 'SOMBRE': [115],
        'TEASING': [140, 155], 'PROUD': [150],
    },
    'Msn3Reward': {'WEARY': [10, 15], 'CONCERNED': [20, 30]},
    'Msn4Offer': {
        'CONCERNED': [10, 20, 40, 65], 'SARDONIC': [30, 50],
        'URGENT': [62], 'PANICKED': [67], 'WEARY': [70], 'RELIEVED': [80],
    },
    'Msn4Reward': {
        'TEASING': [30, 55, 80], 'STERN': [40, 90], 'WARM': [45],
        'AMUSED': [70], 'CONCERNED': [110], 'REASSURING': [120], 'WEARY': [130],
    },
    'Msn4Final': {
        'WARM': [10], 'SARDONIC': [20], 'REASSURING': [30, 50],
        'CONCERNED': [40, 60], 'ANGRY': [80], 'SHOCKED': [100],
        'UNCERTAIN': [130], 'WEARY': [140],
    },
    'Msn5Offer': {
        'TEASING': [20], 'STERN': [30, 160], 'WEARY': [50, 70],
        'CONCERNED': [60, 140], 'AMUSED': [90], 'SARDONIC': [100, 210],
    },
    'Msn5Piratebar': {
        'WARM': [10, 90, 130, 140], 'WEARY': [20, 50], 'ANGRY': [30],
        'PROUD': [40], 'UNCERTAIN': [60], 'EXCITED': [55, 100, 110],
        'CONCERNED': [120],
    },
    'Msn5Detroit': {
        'DRY': [20], 'SARDONIC': [30, 60, 70, 80], 'CONCERNED': [40],
    },
    'Msn5Equip': {
        'RELIEVED': [10], 'CONCERNED': [20, 80], 'ANGRY': [40, 70],
        'URGENT': [90], 'SARDONIC': [140], 'THREATENING': [150],
    },
    'Msn6Offer': {
        'STERN': [30, 70, 120], 'CONCERNED': [50, 80], 'SARDONIC': [60, 150],
        'EXCITED': [110], 'REASSURING': [130],
    },
    'Msn6Briefieng': {
        'STERN': [10, 40, 280], 'WEARY': [20], 'ANGRY': [30, 100],
        'UNCERTAIN': [80, 230], 'SARDONIC': [110, 190, 240, 270],
        'REASSURING': [200], 'CONCERNED': [220], 'SHOCKED': [260],
    },
    'Msn6Mount': {
        'SARDONIC': [10, 70], 'CONCERNED': [30, 50], 'EXCITED': [60],
        'REASSURING': [80], 'WEARY': [90],
    },
    'Msn6LabLand': {'URGENT': [10], 'UNCERTAIN': [20], 'STERN': [30]},
    'Msn6LabRoom': {'SHOCKED': [10], 'URGENT': [20]},
    'Msn6TorpedoAlert': {'ALARMED': [10], 'URGENT': [20, 50]},
    'Msn6OrderDeck': {'PROUD': [20]},
    'Msn6Prison': {
        'UNCERTAIN': [20], 'THREATENING': [30], 'REASSURING': [50, 65, 145, 170],
        'CONCERNED': [70, 160], 'WEARY': [80], 'ANGRY': [110, 120],
        'TEASING': [150, 180], 'AMUSED': [190],
    },
    'Msn6Freeport': {
        'SOMBRE': [10], 'CONCERNED': [20], 'STERN': [30, 80], 'SARDONIC': [70],
    },
    'Msn7Offer': {'UNCERTAIN': [40], 'SARDONIC': [110]},
    'Msn7Cadiz': {
        'THREATENING': [30, 40], 'ANGRY': [50], 'DRY': [60], 'URGENT': [65],
    },
    'Msn7Omega13': {
        'ALARMED': [10, 15, 50, 55], 'SHOCKED': [30, 35], 'DRY': [20, 40, 60],
        'PANICKED': [100],
    },
    'Msn7Battleship': {
        'URGENT': [10, 40, 80, 90], 'SARDONIC': [20, 50, 110],
        'THREATENING': [70, 150, 180], 'SHOCKED': [100], 'ANGRY': [120],
        'REASSURING': [140], 'WEARY': [160, 170],
    },
    'Msn7CheckArtifact': {
        'TEASING': [10], 'PROUD': [20], 'WARM': [30, 40], 'EXCITED': [50],
        'SARDONIC': [70], 'THREATENING': [80], 'UNCERTAIN': [90],
    },
    'Msn7Reward': {'WARM': [10, 50], 'DISGUSTED': [20], 'WEARY': [60]},
    'Msn8Offer': {
        'CONCERNED': [20], 'WARM': [40, 50], 'WEARY': [80, 140, 430],
        'STERN': [90, 180, 350], 'SARDONIC': [170, 320, 340, 420],
        'ANGRY': [310, 380], 'DISGUSTED': [370], 'TEASING': [435, 440, 450],
    },
    'Msn8Osiris': {
        'UNCERTAIN': [10], 'WARM': [30], 'WEARY': [40, 350], 'STERN': [50, 130, 170],
        'CONCERNED': [150, 160, 200], 'ANGRY': [220, 250, 260],
        'REASSURING': [240, 340], 'SOMBRE': [280, 320, 330],
        'FURIOUS': [310], 'THREATENING': [345],
    },
    'Msn8PrinceWales': {'URGENT': [10], 'UNCERTAIN': [20, 40]},
    'Msn8Sprague': {
        'WARM': [10, 20, 30], 'EXCITED': [60], 'CONCERNED': [70, 90, 110],
        'SARDONIC': [100], 'WEARY': [160],
    },
    'Msn9DeckCutscene': {
        'CONCERNED': [30], 'TEASING': [40, 60], 'STERN': [50],
    },
    'Msn9YokohamaCutscene': {
        'CONCERNED': [10, 20, 30, 90, 140, 180], 'TEASING': [50, 80, 110, 190],
        'WARM': [60], 'AMUSED': [100], 'REASSURING': [130, 200],
    },
    'Msn9OrderCutscene': {
        'REFLECTIVE': [20, 30, 80, 190], 'WARM': [40, 50, 60, 70, 200],
        'DRY': [100, 150, 230], 'STERN': [110, 130], 'SARDONIC': [120, 140, 240],
        'SHOCKED': [160], 'DETERMINED': [180], 'WEARY': [270],
        'ANGRY': [350], 'SOMBRE': [360],
    },
    'Msn9RewardCutscene': {
        'ANGRY': [10, 30], 'STERN': [20], 'REASSURING': [40],
        'SARDONIC': [100], 'REFLECTIVE': [110],
    },
    'Msn10OfferCutscene': {
        'STERN': [20, 40], 'CONCERNED': [60, 260], 'SARDONIC': [70, 90, 170, 250],
        'SOMBRE': [150, 160], 'WEARY': [190, 200], 'TEASING': [240],
    },
    'Msn10RescuedCutscene': {
        'RELIEVED': [10], 'TEASING': [20, 120, 150, 160], 'EXCITED': [30],
        'SHOCKED': [40], 'WARM': [50, 90], 'AMUSED': [70], 'URGENT': [80],
        'DETERMINED': [170],
    },
    'Msn10FinalCutscene': {
        'TEASING': [10, 130], 'SOMBRE': [20, 105, 120, 230], 'STERN': [30],
        'UNCERTAIN': [50], 'WEARY': [60], 'DISGUSTED': [90],
        'CONCERNED': [100, 240], 'DETERMINED': [140], 'WARM': [200],
        'SARDONIC': [210, 220],
    },
    'Msn11AmbushCutscene': {
        'STERN': [10, 40, 220], 'SARDONIC': [50, 210], 'CONCERNED': [60, 70, 120, 160],
        'DISGUSTED': [80, 100, 110, 150], 'SHOCKED': [130, 250],
        'DETERMINED': [170, 180], 'REASSURING': [200], 'UNCERTAIN': [205],
        'WEARY': [230], 'URGENT': [260], 'SOMBRE': [280, 290],
    },
    'Msn11DrinkCutscene': {
        'CONCERNED': [10, 20], 'ANGRY': [30], 'UNCERTAIN': [40],
        'STERN': [50], 'WEARY': [60, 120, 140, 150, 160, 170],
        'WARM': [110, 210, 220, 230], 'REASSURING': [130, 190, 200],
        'REFLECTIVE': [180, 240, 260], 'TEASING': [250],
    },
    'Msn12SpragueCutscene': {
        'STERN': [10, 20, 30, 80], 'CONCERNED': [40, 70, 100, 120],
        'URGENT': [50], 'SARDONIC': [60], 'SHOCKED': [140, 150, 180],
        'ALARMED': [190, 250, 260, 280], 'ANGRY': [270, 310],
        'SOMBRE': [300], 'DETERMINED': [320],
    },
    'Msn12CapturedCutscene': {
        'ANGRY': [30], 'THREATENING': [40], 'URGENT': [50], 'DRY': [60, 70],
        'SOMBRE': [150], 'SHOCKED': [160], 'FURIOUS': [170],
        'DETERMINED': [180, 200, 210], 'SARDONIC': [190],
    },
    'Msn13OsirisCutscene': {
        'URGENT': [10], 'CONCERNED': [20, 30, 100, 230], 'COMMAND': [120],
        'TEASING': [200, 210, 270], 'DETERMINED': [220, 260], 'WARM': [240, 280],
    },
    'TrentRescuedCutscene': {
        'UNCERTAIN': [10, 30, 230], 'WARM': [20], 'PROUD': [40],
        'SHOCKED': [50, 80, 150, 280], 'TEASING': [60, 270], 'CONCERNED': [110, 240, 275, 290],
        'SOMBRE': [120, 160, 170, 190, 200], 'URGENT': [220, 250], 'DETERMINED': [300],
    },
    'OdjaIntroCutscene': {
        'PROUD': [50, 60], 'SARDONIC': [70], 'REASSURING': [90],
    },
    'KyotoCutscene': {
        'EXCITED': [10, 20], 'WARM': [30, 40], 'SARDONIC': [60],
        'DETERMINED': [70, 80], 'COMMAND': [130, 150],
    },
    'HokkaidoCutscene': {
        'TEASING': [10, 70, 80], 'WARM': [20, 180, 200],
        'SARDONIC': [30, 60, 90, 160], 'CONCERNED': [100, 110, 120, 150],
        'WEARY': [130], 'PROUD': [140], 'AMUSED': [190],
    },
    'TripoliScene': {
        'UNCERTAIN': [20], 'CONCERNED': [70], 'SARDONIC': [80],
        'AMUSED': [90], 'WARM': [120],
    },
    'JackMeetScene': {
        'ANGRY': [20, 40, 90], 'THREATENING': [30, 110], 'URGENT': [50, 200],
        'UNCERTAIN': [60], 'AMUSED': [80], 'TEASING': [100], 'REASSURING': [120],
        'CONCERNED': [130, 140], 'SARDONIC': [150], 'DETERMINED': [170, 190],
    },
}
