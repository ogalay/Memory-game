from pictures_collection.pokepedia_scraper import Scraper

data_dir = 'Images/Pokemon'
pkm_scraper = Scraper()
pkm_scraper.get_all_images(directory=data_dir)
