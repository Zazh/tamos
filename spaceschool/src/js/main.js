import "../css/main.css";
import Alpine from "alpinejs";
import collapse from "@alpinejs/collapse";
import { registerStarfield } from "./starfield.js";
import { registerGlass } from "./glass.js";

Alpine.plugin(collapse);
registerStarfield(Alpine);
registerGlass(Alpine);


window.Alpine = Alpine;
Alpine.start();
