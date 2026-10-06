// Home page carousel photos (frontend/public/hero/). All from Wikimedia Commons; see public/hero/CREDITS.md.
// CC BY and CC BY-SA require credit, so the carousel shows the author and license for the photo on screen.

export interface HeroSlide {
  src: string
  alt: string
  author: string
  license: string
  licenseUrl: string
  source: string
}

export const HERO_SLIDES: HeroSlide[] = [
  {
    src: '/hero/football-players.jpg',
    alt: 'Yale football players walking onto the field at the Yale Bowl',
    author: 'Kenneth Zirkel',
    license: 'CC BY-SA 3.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0',
    source: 'https://commons.wikimedia.org/wiki/File:2019_Yale_Bulldogs_football_players.jpg',
  },
  {
    src: '/hero/old-campus.jpg',
    alt: "Students walking across Yale's Old Campus past Phelps Gate",
    author: 'DimiTalen',
    license: 'CC0',
    licenseUrl: 'https://creativecommons.org/publicdomain/zero/1.0/deed.en',
    source: 'https://commons.wikimedia.org/wiki/File:Old_Campus_Courtyard_and_Durfee_Hall,_Yale_University,_New_Haven,_2007.jpg',
  },
  {
    src: '/hero/cheerleaders.jpg',
    alt: 'Yale cheerleaders with pom-poms on the field at the Yale Bowl',
    author: 'Kenneth Zirkel',
    license: 'CC BY-SA 3.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0',
    source: 'https://commons.wikimedia.org/wiki/File:Yale_University_Cheerleaders.jpg',
  },
  {
    src: '/hero/ingalls-hockey.jpg',
    alt: 'A hockey game under the arched roof of Ingalls Rink',
    author: 'Quintin Soloviev',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0',
    source: 'https://commons.wikimedia.org/wiki/File:Ingalls_Ice_Rink_(Yale_Hockey).jpg',
  },
  {
    src: '/hero/marching-band.jpg',
    alt: 'The Yale Precision Marching Band performing on the field at the Yale Bowl',
    author: 'Kenneth Zirkel',
    license: 'CC BY-SA 3.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0',
    source: 'https://commons.wikimedia.org/wiki/File:Yale_Precision_Marching_Band_play_Yale_Bowl.jpg',
  },
]
