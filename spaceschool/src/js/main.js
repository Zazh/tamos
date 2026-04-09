import "../css/main.css";
import Alpine from "alpinejs";
import { registerStarfield } from "./starfield.js";

registerStarfield(Alpine);

window.Alpine = Alpine;
Alpine.start();
