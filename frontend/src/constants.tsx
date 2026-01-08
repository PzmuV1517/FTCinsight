export const PROD = process.env.PROD === "True";

// undici bug requires 127.0.0.1 instead of localhost
export const BACKEND_URL = PROD
  ? "https://api.ftcinsight.org/v3/site"
  : "http://127.0.0.1:8000/v3/site";

// Disable bucket in dev mode - bucket doesn't exist yet
export const BUCKET_URL = PROD
  ? "https://storage.googleapis.com/ftcinsight_v1"
  : "";

// FTC Season Configuration
export const CURR_YEAR = 2026; // DECODE season (2025-2026)
export const CURR_WEEK = 1;

// Minimum FTC team number (teams start from higher numbers in FTC)
export const MIN_TEAM_NUM = 1;

// Placeholder teams (adjust as needed for FTC)
export const PLACEHOLDER_TEAMS = Array.from({ length: 30 }, (_, i) => 99970 + i);

// Years with detailed score breakdowns
export const BREAKDOWN_YEARS = [2019, 2020, 2021, 2022, 2023, 2024];

// FTC Tiebreaker Point names by season (equivalent to FRC's RP_NAMES)
// FTC uses TBP (Tie Breaker Points) instead of Ranking Points
export const RP_NAMES: { [key: number]: string[] } = {
  2026: ["TBP1", "TBP2", "TBP3"], // Future season
  2025: ["TBP1", "TBP2", "TBP3"], // INTO THE DEEP (current)
  2024: ["TBP1", "TBP2"], // INTO THE DEEP
  2023: ["TBP1", "TBP2"], // CENTERSTAGE
  2022: ["TBP1", "TBP2"], // POWERPLAY
  2021: ["TBP1", "TBP2"], // FREIGHT FRENZY
  2020: ["TBP1", "TBP2"], // ULTIMATE GOAL
  2019: ["TBP1", "TBP2"], // SKYSTONE
  2018: ["TBP1", "TBP2"], // ROVER RUCKUS
  2017: ["TBP1", "TBP2"], // RELIC RECOVERY
  2016: ["TBP1", "TBP2"], // VELOCITY VORTEX
};

// Helper to safely get RP names with fallback
export const getRPName = (year: number, index: number): string => {
  const names = RP_NAMES[year] || RP_NAMES[2025] || ["TBP1", "TBP2", "TBP3"];
  return names[index] || `TBP${index + 1}`;
};

export const CORRECT_COLOR = "#86CFA3";
export const INCORRECT_COLOR = "#F77F84";

export const Category10Colors = [
  "#1f77b4",
  "#ff7f0e",
  "#2ca02c",
  "#d62728",
  "#9467bd",
  "#8c564b",
  "#e377c2",
  "#7f7f7f",
  "#bcbd22",
  "#17becf",
];

// FTC Game Names by Season (year represents the start of the season)
export const FTC_GAMES: { [key: number]: string } = {
  2024: "INTO THE DEEP",
  2023: "CENTERSTAGE",
  2022: "POWERPLAY",
  2021: "FREIGHT FRENZY",
  2020: "ULTIMATE GOAL",
  2019: "SKYSTONE",
  2018: "ROVER RUCKUS",
  2017: "RELIC RECOVERY",
  2016: "VELOCITY VORTEX",
};

// FTC Event Types
export const FTC_EVENT_TYPES: { [key: string]: string } = {
  scrimmage: "Scrimmage",
  league_meet: "League Meet",
  qualifier: "Qualifier",
  league_tournament: "League Tournament",
  championship: "Championship",
  super_qualifier: "Super Qualifier",
  regional_championship: "Regional Championship",
  first_championship: "FIRST Championship",
  offseason: "Offseason",
  other: "Other",
};

// FTC Score Components by Season
export const SCORE_COMPONENTS: { [key: number]: { key: string; name: string }[] } = {
  2024: [
    // INTO THE DEEP
    { key: "auto_net_samples", name: "Auto Net Samples" },
    { key: "auto_low_basket", name: "Auto Low Basket" },
    { key: "auto_high_basket", name: "Auto High Basket" },
    { key: "auto_low_chamber", name: "Auto Low Chamber" },
    { key: "auto_high_chamber", name: "Auto High Chamber" },
    { key: "teleop_net_samples", name: "TeleOp Net Samples" },
    { key: "teleop_low_basket", name: "TeleOp Low Basket" },
    { key: "teleop_high_basket", name: "TeleOp High Basket" },
    { key: "teleop_low_chamber", name: "TeleOp Low Chamber" },
    { key: "teleop_high_chamber", name: "TeleOp High Chamber" },
    { key: "ascent_1", name: "Robot 1 Ascent" },
    { key: "ascent_2", name: "Robot 2 Ascent" },
  ],
  2023: [
    // CENTERSTAGE
    { key: "auto_backstage", name: "Auto Backstage Pixels" },
    { key: "auto_backdrop", name: "Auto Backdrop Pixels" },
    { key: "purple_pixel_1", name: "Purple Pixel 1" },
    { key: "purple_pixel_2", name: "Purple Pixel 2" },
    { key: "yellow_pixel_1", name: "Yellow Pixel 1" },
    { key: "yellow_pixel_2", name: "Yellow Pixel 2" },
    { key: "teleop_backstage", name: "TeleOp Backstage" },
    { key: "teleop_backdrop", name: "TeleOp Backdrop" },
    { key: "mosaics", name: "Mosaics" },
    { key: "set_line", name: "Set Lines" },
    { key: "drone_1", name: "Drone 1" },
    { key: "drone_2", name: "Drone 2" },
    { key: "park_1", name: "Endgame Park 1" },
    { key: "park_2", name: "Endgame Park 2" },
  ],
  2022: [
    // POWERPLAY
    { key: "auto_terminal", name: "Auto Terminal" },
    { key: "auto_junctions", name: "Auto Junction Cones" },
    { key: "auto_navigated", name: "Auto Navigated" },
    { key: "teleop_terminal_near", name: "TeleOp Terminal Near" },
    { key: "teleop_terminal_far", name: "TeleOp Terminal Far" },
    { key: "teleop_junctions", name: "TeleOp Junction Cones" },
    { key: "owned_junctions", name: "Owned Junctions" },
    { key: "beacon_junctions", name: "Beacon Junctions" },
    { key: "circuit", name: "Circuit" },
  ],
  2021: [
    // FREIGHT FRENZY
    { key: "auto_carousel", name: "Auto Carousel" },
    { key: "auto_storage", name: "Auto Storage Freight" },
    { key: "auto_freight", name: "Auto Freight" },
    { key: "auto_parked", name: "Auto Parked" },
    { key: "teleop_storage", name: "TeleOp Storage" },
    { key: "teleop_freight", name: "TeleOp Freight" },
    { key: "shared_freight", name: "Shared Freight" },
    { key: "delivered", name: "Delivered" },
    { key: "capped", name: "Capped" },
    { key: "endgame_parked", name: "Endgame Parked" },
  ],
  2020: [
    // ULTIMATE GOAL
    { key: "auto_wobble", name: "Auto Wobble Goals" },
    { key: "auto_powershots", name: "Auto Power Shots" },
    { key: "auto_tower", name: "Auto Tower" },
    { key: "auto_navigated", name: "Auto Navigated" },
    { key: "teleop_tower", name: "TeleOp Tower" },
    { key: "endgame_wobble", name: "Endgame Wobble Goals" },
    { key: "endgame_rings", name: "Endgame Wobble Rings" },
    { key: "endgame_powershots", name: "Endgame Power Shots" },
  ],
  2019: [
    // SKYSTONE
    { key: "auto_delivered", name: "Auto Delivered" },
    { key: "auto_skystones", name: "Auto Skystones" },
    { key: "auto_placed", name: "Auto Placed" },
    { key: "auto_navigated", name: "Auto Navigated" },
    { key: "teleop_delivered", name: "TeleOp Delivered" },
    { key: "teleop_placed", name: "TeleOp Placed" },
    { key: "skyscraper", name: "Tallest Skyscraper" },
    { key: "foundation_moved", name: "Foundation Moved" },
    { key: "capstone", name: "Capstone" },
  ],
};

// FTC Region mappings
export const FTC_REGIONS: { [key: string]: string } = {
  USAK: "Alaska",
  USAL: "Alabama",
  USAR: "Arkansas",
  USAZ: "Arizona",
  USCALA: "California - Los Angeles",
  USCANO: "California - NorCal",
  USCASD: "California - San Diego",
  USCO: "Colorado",
  USCT: "Connecticut",
  USDE: "Delaware",
  USFL: "Florida",
  USGA: "Georgia",
  USHI: "Hawaii",
  USIA: "Iowa",
  USID: "Idaho",
  USIL: "Illinois",
  USIN: "Indiana",
  USKS: "Kansas",
  USKY: "Kentucky",
  USLA: "Louisiana",
  USMA: "Massachusetts",
  USMD: "Maryland",
  USMI: "Michigan",
  USMN: "Minnesota",
  USMO: "Missouri",
  USMS: "Mississippi",
  USMT: "Montana",
  USNC: "North Carolina",
  USND: "North Dakota",
  USNE: "Nebraska",
  USNH: "New Hampshire",
  USNJ: "New Jersey",
  USNM: "New Mexico",
  USNV: "Nevada",
  USNYEX: "New York - Excelsior",
  USNYLI: "New York - Long Island",
  USNYNYC: "New York - NYC",
  USOH: "Ohio",
  USOK: "Oklahoma",
  USOR: "Oregon",
  USPA: "Pennsylvania",
  USRI: "Rhode Island",
  USSC: "South Carolina",
  USTN: "Tennessee",
  USTXCE: "Texas - Central",
  USTXHO: "Texas - Houston",
  USTXNO: "Texas - North",
  USTXSO: "Texas - South",
  USTXWP: "Texas - West/Panhandle",
  USUT: "Utah",
  USVA: "Virginia",
  USVT: "Vermont",
  USWA: "Washington",
  USWI: "Wisconsin",
  USWV: "West Virginia",
  USWY: "Wyoming",
  CAAB: "Alberta",
  CABC: "British Columbia",
  CAMB: "Manitoba",
  CAON: "Ontario",
  CAQC: "Quebec",
};

// Empty event name map for FTC (can be customized)
export const eventNameMap: { [key: string]: string } = {};

// Empty division mapping for FTC (FTC doesn't have the same division structure as FRC)
export const divisionToMainEvent: { [key: string]: string } = {};
export const mainEventToDivisions: { [key: string]: { name: string; key: string }[] } = {};
