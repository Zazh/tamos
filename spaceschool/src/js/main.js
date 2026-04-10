import "../css/main.css";
import Alpine from "alpinejs";
import collapse from "@alpinejs/collapse";
import { registerStarfield } from "./starfield.js";

Alpine.plugin(collapse);
registerStarfield(Alpine);


window.Alpine = Alpine;
Alpine.start();
