// HTML canvas frontend to display games
// Certain elements may be poorly designed/structured, but this just needs to 
// take some board representation & display it
/* --------------------- CONSTANTS & GLOBALS --------------------- */
const SERVE_URL = "ws://localhost:8080";
// const PING_INTERVAL = 2; // seconds
const TOKEN_RATIO = 1 / 16;  // ratio of chance token size to board size
const BORDER_RATIO = 0.05; // ratio of border to board size
const ASPECT_RATIO = 16/9;
const DRAWING_SCALE = 16;

const IMG_PATH = './static/img/';
const RES_IMGS = ['brick_hex.png', 'grain_hex.png', 'lumber_hex.png', 
    'ore_hex.png', 'wool_hex.png', 'desert_hex.png'];
const DEV_IMGS = ['knight_dev.png', 'victory_pnt_dev.png', 'road_dev.png', 
    'monopoly_dev.png', 'year_of_plenty_dev.png'];
// Number of dots shown for each dice sum 
//                   2  3  4  5  6     8  9  10 11 12
const CHANCE_DOTS = [1, 2, 3, 4, 5, 0, 5, 4, 3, 2, 1];
const RLENS = [3, 4, 5, 4, 3];  // row lengths
let canvas;
let ctx;
let gameBoard;
let initialized_board = false;

const map_hex_idx_to_row_col = [
    [10, 7],
    [10, 11],
    [10, 15],
    [8, 5],
    [8, 9],
    [8, 13],
    [8, 17],
    [6, 3],
    [6, 7],
    [6, 11],
    [6, 15],
    [6, 19],
    [4, 5],
    [4, 9],
    [4, 13],
    [4, 17],
    [2, 7],
    [2, 11],
    [2, 15],
]
const RMAP = [
    0,
    0b00000000000000010101010101000000,
    0b00000000000000100010001000100000,
    0b00000000000001010101010101010000,
    0b00000000000010001000100010001000,
    0b00000000000101010101010101010100,
    0b00000000001000100010001000100010,
    0b00000000000101010101010101010100,
    0b00000000000010001000100010001000,
    0b00000000000001010101010101010000,
    0b00000000000000100010001000100000,
    0b00000000000000010101010101000000,
    0]
/* const BMAP = [
    0,
    0b00000000000000101010101010100000,
    0,
    0b00000000000010101010101010101000,
    0,
    0b00000000001010101010101010101010,
    0,
    0b00000000001010101010101010101010,
    0,
    0b00000000000010101010101010101000,
    0,
    0b00000000000000101010101010100000,
    0,
] */
// Load images
/*
    * Brick 'B'
    * Grain 'G'
    * Lumber 'L'
    * Ore 'O'
    * Wool 'W'
    * Desert 'D'
    */
const HEX_IMAGES = {
    "B": new Image(),
    "G": new Image(),
    "L": new Image(),
    "O": new Image(),
    "W": new Image(),
    "D": new Image(),
};
Object.keys(HEX_IMAGES).forEach((key, idx) => {
    HEX_IMAGES[key].src = IMG_PATH + RES_IMGS[idx];
});
const RES_NAMES = {
    "B": "Brick",
    "G": "Grain",
    "L": "Lumber",
    "O": "Ore",
    "W": "Wool",
}
const DEV_IMAGES = {
    "K": new Image(),
    "V": new Image(),
    "R": new Image(),
    "M": new Image(),
    "Y": new Image(),
};
Object.keys(DEV_IMAGES).forEach((key, idx) => {
    DEV_IMAGES[key].src = IMG_PATH + DEV_IMGS[idx];
});
const DEV_NAMES = {
    "K": "Knight",
    "V": "Victory\nPoint",
    "R": "2 Roads",
    "M": "Monopoly",
    "Y": "Year of\nPlenty",
};
const LRGST_ARMY_IMG = new Image();
LRGST_ARMY_IMG.src = IMG_PATH + 'largestarmy_vp.png';
const LNGST_ROAD_IMG = new Image();
LNGST_ROAD_IMG.src = IMG_PATH + 'longestroad_vp.png';
const PORT_SHIP = new Image();
PORT_SHIP.src = IMG_PATH + 'portship.svg';
const PORT_DOCKS = new Image();
PORT_DOCKS.src = IMG_PATH + 'portdocks.png';

const COLORS = ["#00ffff", "#ffffff", "#a500ff", "#00ffa5"];
const HAND_OFFSET = [0, 25, 50, 75]
// Current representation of current board state (read: board state object)
let brd_s_o = {
    "game_cycle_status": 0,
    "num_players": 4,
    // Static string states not used for internal game state representation
    // Board state representation (currently static, filled with arbitrary board)
    // "hex_state": "PGBPGMFMFDFGBPBGFPM",
    "curr_turn": 0,
    "hex_state": "WGBWGOLOLDLGBWBGLWO",

    // hex codes for different chance values, 0 means no token (desert)
    tkn_state: "B655438830B9A46C92A",
    // orientation values for ports at each hex idx, 6 means no port
    port_orients: "6343665266661665610",
    // port types for port at each above non-6 hex idx
    port_type_state: "554053215", //# "6005661066664663620",

    // Varying game state elements
    "robber_loc": 9,
    "dv1": 3,
    "dv2": 6,
    "bank": [13,10,10,15,18,
             7,3,2,0,1,
             0,0,
             ],
    hands: [2,1,3,1,2,
           2,0,0,0,0,
           0,0,1,0,0,
           0,0,0,0,0,
           5,
           
           2,6,0,2,0,
           0,1,0,1,0,
           0,0,0,0,0,
           0,0,0,0,0,
           5,

           3,1,0,2,0,
           1,1,0,0,0,
           0,1,0,0,0,
           0,0,0,0,0,
           7, 
           0,2,7,0,0,
           0,0,0,1,1,
           1,0,3,0,0,
           0,0,0,0,0,
           8,
           ],

    btypemap: [
        0,
        0b00000000000000000010000000000000,
        0,
        0b00000000000000000000000000000000,
        0,
        0b00000000000000000000000000100000, 
        0,
        0b00000000000000000000000000000000, 
        0,
        0b00000000000000000000000000001000,
        0,
        0b00000000000000000000000000000000,
        0,
    ],
    rbmap0: [
       0, 
        0b00000000000000110111011000000000,
        0b00000000000000100000000000000000, 
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000,
        0b00000000000000100000000000000000,
        0b00000000000000110000000000000000,
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000,
        0,
    ],
    rbmap1: [
       0, 
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000, 
        0b00000000000000000000000111011000,
        0b00000000000000000000000010001000, 
        0b00000000000000000000000001110000, 
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000,
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0,
    ],
    rbmap2: [
       0, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000111011101100000000000, 
        0b00000000001000000000000000000000,
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000001011000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0,
    ],
    rbmap3: [
       0, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0b00000000001100000000000011010110, 
        0b00000000000010000000000000001000, 
        0b00000000000010000000000000001000,
        0b00000000000000000000000000000000, 
        0b00000000000000000000000000000000, 
        0,
    ],
}
// Track mouse position
const mouse = {
    x: 0,
    y: 0,
}

/* --------------------- Main Display Logic --------------------- */
// window.onload waits for whole page to load before running; as opposed to 
// document.onload which waits for DOM to be ready
window.onload = function () {
    let socket = new WebSocket(SERVE_URL);
    gen_socket_listeners(socket);

    canvas = document.getElementById("canvas1");
    ctx = canvas.getContext('2d');
    // Establish dimensions of canvas; maximize screen space
    if (window.innerWidth < window.innerHeight*ASPECT_RATIO) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerWidth/ASPECT_RATIO;
    } else {
        canvas.width = window.innerHeight*ASPECT_RATIO;
        canvas.height = window.innerHeight;
    }
    gameBoard = new GameBoard(canvas, 1000*ASPECT_RATIO, 1000);  // arbitrary vals
    gameBoard.resize();
}
window.addEventListener('resize', function () {
    gameBoard.resize();
});
window.addEventListener('mousemove', function(e) {
    mouse.x = e.x;
    mouse.y = e.y;
    // TODO: when hovering over a game element, highlight it
});

// function handleActButtonClick(event) {
// }

const map_hex_to_unique_edges = [
    6, 6, 0,
    4, 1, 1, 5,
    6, 6, 6, 6, 0,
    3, 1, 1, 2,
    6, 6, 0,
    ];
const map_hex_to_unique_vertices = [
    6, 6, 0,
    3, 5, 5, 4,
    6, 6, 6, 6, 0,
    2, 5, 5, 1,
    6, 6, 0,
    ];

function hex_rc_to_edge_rc(hex_rc, side_idx) {
    switch(side_idx) {
        case 0:
            return [hex_rc[0]-1, hex_rc[1]+1];
        case 1:
            return [hex_rc[0]-1, hex_rc[1]-1];
        case 2:
            return [hex_rc[0], hex_rc[1]-2];
        case 3:
            return [hex_rc[0]+1, hex_rc[1]-1];
        case 4:
            return [hex_rc[0]+1, hex_rc[1]+1];
        case 5:
            return [hex_rc[0], hex_rc[1]+2];
    }
}

function hex_rc_to_vertex_rc(hex_rc, vertex_idx) {
    switch(vertex_idx) {
        case 0:
            return [hex_rc[0]-1, hex_rc[1]+2];
        case 1:
            return [hex_rc[0]-1, hex_rc[1]];
        case 2:
            return [hex_rc[0]-1, hex_rc[1]-2];
        case 3:
            return [hex_rc[0]+1, hex_rc[1]-2];
        case 4:
            return [hex_rc[0]+1, hex_rc[1]];
        case 5:
            return [hex_rc[0]+1, hex_rc[1]+2];
    }
}
/*
    * Class representing game board & all game components to render
    * Contains arrays of all board subcomponents to render
    * staticComps: array of underlying unchanging board components
    * components: game pieces, which can change during game (e.g. roads, robber)
    */
class GameBoard {
    constructor(canvas, renderWidth, renderHeight) {
        this.canvas = canvas;
        this.ctx = this.canvas.getContext('2d');
        this.renderWidth = renderWidth;
        this.renderHeight = renderHeight;
        this.wFactor = this.canvas.width / this.renderWidth;
        this.wrFactor = this.renderWidth / this.canvas.width;
        this.hFactor = this.canvas.height / this.renderHeight;
        this.hrFactor = this.renderHeight / this.canvas.height;
        this.components = [];
        this.staticComps = [];
        this.borderWidth = Math.floor(this.renderWidth * BORDER_RATIO);  // err lower
        // this.bodyWidth = this.renderWidth - this.borderWidth * 2;
        this.bodyHeight = this.renderHeight - this.borderWidth * 2;
        this.hexW = this.bodyHeight / 5;
        this.tileH = this.hexW * (2 / Math.sqrt(3));
        this.rowH = this.tileH * 0.75;
        // uncomment below line to initialize board before establishing connection to server (testing purposes)
        // this.reinit()
        this.active_action = "";
        // TODO: find better method of click detection
        // TODO: create hover lists for each type of clickable item (ports, hexes, vertices, edges)
        this.hoverLists = {
            // Ports list
            "trade_btn": [],
            "trade4_btn": [],
                // Ports (for trading)
                /*{x: 975, y: 925, r: 1, c: 0, id: "p"},
                {x: 640, y: 920, r: 1, c: 1, id: "p"},
                {x: 1220, y: 780, r: 1, c: 2, id: "p"},
                {x: 465, y: 635, r: 1, c: 3, id: "p"},
                {x: 1385, y: 495, r: 1, c: 4, id: "p"},
                {x: 1220, y: 205, r: 1, c: 5, id: "p"},
                {x: 465, y: 355, r: 1, c: 6, id: "p"},
                {x: 975, y: 45, r: 1, c: 7, id: "p"},
                {x: 635, y: 45, r: 1, c: 8, id: "p"},
            ],*/
            // Hexes list
            "robber_btn": [],
            // Vertices list (used with settlement_btn & city_btn)
            "settlement_btn": [],
            "road_btn": [],
            "dev_card_btn": [],
        }

        let port_num = 0;
        let brd_cx = this.renderWidth / 2;
        let brd_cy = this.renderHeight / 2;
        // Iterate over hexes
        for(let idx = 0; idx < 19; idx++) {
            let hexCX = hex_center_x(this.hexW, brd_cx, idx);
            let hexCY = hex_center_y(this.tileH, brd_cy, idx);
            // Ports list for bank trades
            if(brd_s_o.port_orients[idx] !== '6') {
                let port_orient = parseInt(brd_s_o.port_orients[idx]);
                this.hoverLists.trade_btn.push({
                    x: hex_port_x(this.hexW, hexCX, port_orient),
                    y: hex_port_y(this.tileH, hexCY, port_orient),
                    r: port_num,
                    c: parseInt(brd_s_o.port_type_state[port_num]),
                    id: "p",
                });
                port_num++;
            }

            // Hex locations for robber
            this.hoverLists.robber_btn.push({
                x: hexCX,
                y: hexCY,
                r: idx,
                c: 0,
                id: "h"  // hex, clickable for placing robber
            });

            // For each hex, add vertices
            let v_ids = [];
            switch(map_hex_to_unique_vertices[idx]) {
                case 0:  // all vertices
                    v_ids = [0, 1, 2, 3, 4, 5];
                    break;
                case 1:  // just vertex 0
                    v_ids = [0];
                    break;
                case 2:  // just vertex 2
                    v_ids = [2];
                    break;
                case 3:  // just vertex 3
                    v_ids = [3];
                    break;
                case 4:  // just vertex 5
                    v_ids = [5];
                    break;
                case 6: // all vertices except for west side
                    v_ids = [1, 2, 3, 4];
                    break;
                default: // no vertices (case 5 included)
            }
            for(let i = 0; i < v_ids.length; i++) {
                this.hoverLists.settlement_btn.push({
                    x: hex_corner_x(this.hexW, hexCX, v_ids[i]),
                    y: hex_corner_y(this.tileH, hexCY, v_ids[i]),
                    r: hex_rc_to_vertex_rc(map_hex_idx_to_row_col[idx], v_ids[i])[0],
                    c: hex_rc_to_vertex_rc(map_hex_idx_to_row_col[idx], v_ids[i])[1],
                    id: "v",
                })
            }

            // For each hex, add edges
            let edge_ids = [];
            switch(map_hex_to_unique_edges[idx]) {
                case 0:  // all edges
                    edge_ids = [0, 1, 2, 3, 4, 5];
                    break;
                case 1: // edges 2 & 5
                    edge_ids = [2, ];
                    break;
                case 2:
                    edge_ids = [2, 5, 0];
                    break;
                case 3:
                    edge_ids = [2, 1];
                    break;
                case 4:
                    edge_ids = [2, 3];
                    break;
                case 5:
                    edge_ids = [2, 5, 4];
                    break;
                case 6:
                    edge_ids = [0, 1, 2, 3, 4];
                    break;
                default:
                    // shouldn't ever occur
            }
            for(let i = 0; i < edge_ids.length; i++) {
                this.hoverLists.road_btn.push({
                    x: hex_side_x(this.hexW, hexCX, edge_ids[i]),
                    y: hex_side_y(this.tileH, hexCY, edge_ids[i]),
                    r: hex_rc_to_edge_rc(map_hex_idx_to_row_col[idx], edge_ids[i])[0],
                    c: hex_rc_to_edge_rc(map_hex_idx_to_row_col[idx], edge_ids[i])[1],
                    id: "e",
                });
            }
        }
    }
    reinit() {
        this.components = [];
        this.staticComps = [];
        this.#addStaticBoardComponents();
        this.addComponents();
    }
    draw() {
        // Redraws full game board with all components
        this.ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < this.staticComps.length; i++) {
            this.staticComps[i].draw(this.ctx, this.wFactor, this.hFactor);
        }
        for (let i = 0; i < this.components.length; i++) {
            this.components[i].draw(this.ctx, this.wFactor, this.hFactor);
        }
        if(this.active_action !== "") {
            if(this.active_action === "city_btn") {
                this.drawHoverList(this.hoverLists.settlement_btn);
            } else if(this.hoverLists.hasOwnProperty(this.active_action)) {
                this.drawHoverList(this.hoverLists[this.active_action]);
            }
        }
    }
    drawHoverList(hoverList) {
        let rad = 25;
        if (this.active_action === "robber_btn" || this.active_action === "trade_btn") {
            rad = 50;
        }
        for(let i = 0; i < hoverList.length; i++) {
            this.ctx.save();
            this.ctx.beginPath();
            this.ctx.arc(hoverList[i].x*this.wFactor, hoverList[i].y*this.hFactor, rad*this.wFactor, 0, 2 * Math.PI);
            this.ctx.fillStyle = "rgba(200, 220, 230, 0.5)";
            this.ctx.fill();
            this.ctx.stroke();
            this.ctx.restore();
        }
    }
    resize() {
        // Construct square of maximum size
        if (window.innerWidth < window.innerHeight*ASPECT_RATIO) {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerWidth/ASPECT_RATIO;
        } else {
            this.canvas.width = window.innerHeight*ASPECT_RATIO;
            this.canvas.height = window.innerHeight;
        }
        // Set scaling factors to redraw game elements at proper size
        this.wFactor = this.canvas.width / this.renderWidth;
        this.wrFactor = this.renderWidth / this.canvas.width;
        this.hFactor = this.canvas.height / this.renderHeight;
        this.hrFactor = this.renderHeight / this.canvas.height;
        this.draw();
    }
    addComponent(item) {
        this.components[this.components.length] = item;
    }
    clearComponents() {
        this.components = [];
    }
    addBoardComponent(item) {
        this.staticComps[this.staticComps.length] = item;
    }
    /*
          * Add all current board elements to object to be displayed
          */
    #addStaticBoardComponents() {
        const cX = this.renderWidth / 2;
        const cY = this.renderHeight / 2;
        const tokenSize = this.bodyHeight * TOKEN_RATIO;
        let cti = 0; // current tile index

        /* 
              * Tile adding order:
              *    19 18 17
              *   16 15 14 13      
              * 12 11 10  9  8
              *   7  6  5  4
              *    3  2  1 
              */
        let port_type_idx = 0;
        for (let y = 0; y < 5; y++) {
            for (let x = 0; x < RLENS[y]; x++) {
                let tileCX = cX + this.hexW * (RLENS[y] / 2 - x - 0.5);
                let tileCY = cY + this.rowH * (2 - y);
                this.addBoardComponent(
                    new Img(
                        tileCX - this.tileH / 2,
                        tileCY - this.tileH / 2,
                        this.tileH,
                        this.tileH,
                        HEX_IMAGES[brd_s_o.hex_state[cti]]));
                if (brd_s_o.tkn_state[cti] !== '0') {
                    this.addBoardComponent(
                        new ChanceToken(
                            tileCX - tokenSize / 2,
                            tileCY - tokenSize / 2,
                            tokenSize,
                            tokenSize,
                            parseInt(brd_s_o.tkn_state[cti], 16),
                            true));
                }
                if (brd_s_o.port_orients[cti] !== '6') {
                    let portside = parseInt(brd_s_o.port_orients[cti]);
                    let sx = hex_side_x(this.hexW, tileCX, portside);
                    let sy = hex_side_y(this.tileH, tileCY, portside);
                    this.addBoardComponent(
                        new Port(sx, sy, this.tileH / 2,
                            portside,
                            parseInt(brd_s_o.port_type_state[port_type_idx])));
                    port_type_idx++;
                }
                cti++;
            }
        }
    }
    addComponents() {
        const tokenSize = this.bodyHeight * TOKEN_RATIO;
        let sx, sy;
        // roads & buildings
        const N_COLS = 23;
        const cX = this.renderWidth/2;
        const cY = this.renderHeight/2;
        let rOrient = -1;
        for(let r = 0; r < RMAP.length; r++) {
            for(let c = 0; c < N_COLS; c++) {
                let col = -1;
                if((brd_s_o.rbmap0[r] & (1<<c)) !== 0) {
                    col = 0;
                } else if((brd_s_o.rbmap1[r] & (1<<c)) !== 0) {
                    col = 1;
                } else if((brd_s_o.rbmap2[r] & (1<<c)) !== 0) {
                    col = 2;
                } else if((brd_s_o.rbmap3[r] & (1<<c)) !== 0) {
                    col = 3;
                }
                if(col > -1) {
                    if((RMAP[r] & (1<<c)) !== 0) {
                        sx = cX + (11-c)*this.hexW*0.25;
                        sy = cY + (r-6)*this.tileH*0.375;
                        if(r%2===0) {
                            rOrient = 2;
                        } else if(c%4===2) {
                            rOrient = (r%4===1) ? 1 : 3;
                        } else if(c%4===0) {
                            rOrient = (r%4===1) ? 3 : 1;
                        } else {
                            rOrient = -1; // this shouldn't occur
                        }
                        this.addComponent(new Road(sx, sy, rOrient, COLORS[col]));
                    } else {
                        sx = cX + (11-c)*this.hexW*0.25;
                        sy = cY + (r-6)*this.tileH*0.375;
                        // offset to vertex
                        if((c%4 === 1 && r%4===1) || (c%4===3 && r%4===3)) {
                            sy += this.tileH*0.125;
                        } else {
                            sy -= this.tileH*0.125;
                        }
                        if((brd_s_o.btypemap[r] & (1<<c)) !== 0) {
                            this.addComponent(new City(sx, sy, COLORS[col]));
                        } else {
                            this.addComponent(new Settlement(sx, sy, COLORS[col]));
                        }
                    }
                }
            }
        }
        // Place robber
        this.addComponent(new Robber(
            hex_center_x(this.hexW, this.renderWidth / 2, brd_s_o.robber_loc),
            hex_center_y(this.tileH, this.renderHeight / 2, brd_s_o.robber_loc)));
        // Add dice
        this.addComponent(new Dice(
            this.renderWidth*0.7, this.renderHeight-this.borderWidth, tokenSize, 
            parseInt(brd_s_o.dv1), parseInt(brd_s_o.dv2)));
        // Show player hands
        const hph = this.renderHeight*0.22;
        let yph = hph * 0.06;
        const xph = yph;
        for (let i = 0; i < brd_s_o["num_players"]; i++) {
            const offset = HAND_OFFSET[i];
            this.addComponent(new PlayerHand(xph, yph, hph, COLORS[i], (brd_s_o.hands[offset+10]===1), (brd_s_o.hands[offset+11]===1), (brd_s_o.hands[offset+20]),
                brd_s_o.hands.slice(offset, offset+5),
                brd_s_o.hands.slice(offset+5, offset+10),
                brd_s_o.hands[offset+15],
                i,
            ));
            yph += hph*1.12;
        }
        // Draw bank
        this.addComponent(new PlayerHand(
            this.renderWidth-hph*2, hph*0.06, hph*1.4, 
            "#00a5ff", 
            (brd_s_o.bank[10]===1), (brd_s_o.bank[11]===1), 0,
            brd_s_o.bank.slice(0, 5),
            brd_s_o.bank.slice(5, 10),
            0,
            -1,
        ));
    }
}


/* --------------------- BOARD COMPONENT CLASSES --------------------- */
/*
    * Each class has a constructor with relevant data, and a draw method with 
    * the params ctx (canvas context), wFactor (width scaling factor), and 
    * hFactor (height scaling factor)
    * The scaling factors are used to render the components with the same 
    * relative size despite canvas resizing
    */
class ChanceToken {
    constructor(x, y, width, height, dice_val) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.dv = dice_val;
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        const radius = wFactor * this.width / 2;
        const centerX = this.x * wFactor + radius;
        const centerY = this.y * hFactor + radius;
        // Shadow, to give depth illusion
        ctx.shadowColor = 'black';
        ctx.shadowBlur = 5;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;
        ctx.beginPath();
        // Base token
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI, false);
        ctx.fillStyle = '#eace9c';
        ctx.fill();
        ctx.closePath();
        ctx.restore();
        ctx.save();

        // Draw dice sum
        ctx.font = `bold ${36*wFactor}px Arial`;
        ctx.fillStyle = (this.dv === 6 || this.dv === 8) ? 'red' : 'black';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.dv, centerX, centerY);

        // Draw dots indicating relative chance 
        const dotRadius = 3 * wFactor;
        const dotInterval = 7 * wFactor;
        for (let i = 0; i < CHANCE_DOTS[this.dv - 2]; i++) {
            ctx.beginPath();
            ctx.arc(centerX - Math.floor(dotInterval * (CHANCE_DOTS[this.dv - 2] / 2 - 0.5)) + i * dotInterval, centerY + radius / 2, dotRadius, 0, 2 * Math.PI, false);
            ctx.fill();
            ctx.closePath();
        }
        ctx.restore();
    }
}
class City {
    constructor(x, y, baseColor) {
        this.cX = x;
        this.cY = y;
        this.baseColor = baseColor;
        const hl = DRAWING_SCALE * 1.2;
        const hw = DRAWING_SCALE;
        const bh = DRAWING_SCALE * 1.2; // base height
        const rh = DRAWING_SCALE * 0.9; // roof height
        // Define 3D object via points, then rotate for perspective
        const preRotateVertices = [
            // Front face (orientation of "near wall" of settlement)
            [-hl, -bh, hw], // ground left
            [-hl, 0, hw],
            [0, 0, hw],  // middle
            [hl / 2, rh, hw], // ridge end
            [hl, 0, hw],
            [hl, -bh, hw],  // ground right
            // Back face
            [-hl, -bh, -hw], // ground left
            [-hl, 0, -hw],
            [0, 0, -hw],  // middle
            [hl / 2, rh, -hw], // ridge end
            [hl, 0, -hw],
            [hl, -bh, -hw],  // ground right
        ];
        this.vertices = preRotateVertices.map(p => rotateAroundOrigin(p, Math.PI / 8, -Math.PI / 8, -0.14));
        // Define faces for simple rendering of visible sides
        this.faces = [
            [1, 2, 8, 7],  // flat roof face
            [0, 1, 2, 3, 4, 5],  // near wall face
            [3, 4, 10, 9],  // near angled roof face
            [5, 4, 10, 11],  // below angled roof wall face
        ];
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        let clr = this.baseColor; //shadeColor(this.baseColor, -30);
        for (const face of this.faces) {
            let startVertex = this.vertices[face[0]];
            ctx.beginPath();
            ctx.moveTo(wFactor * (this.cX + startVertex[0]), hFactor * (this.cY - startVertex[1]));
            for (let v_idx = 1; v_idx < face.length; v_idx++) {
                let endVertex = this.vertices[face[v_idx]];
                ctx.lineTo(wFactor * (this.cX + endVertex[0]), hFactor * (this.cY - endVertex[1]));
                startVertex = endVertex;
            }
            ctx.closePath();
            ctx.fillStyle = clr;
            clr = shadeColor(clr, 30);
            ctx.strokeStyle = shadeColor(this.baseColor, 140);
            ctx.lineWidth = 2 * wFactor;
            ctx.fill();
            ctx.stroke();
        }
        ctx.restore();
    }
}
class Settlement {
    constructor(x, y, baseColor) {
        this.cX = x;
        this.cY = y;
        this.baseColor = baseColor;
        const hl = DRAWING_SCALE * 1.1;
        const hw = DRAWING_SCALE;
        const hh = DRAWING_SCALE * 0.9;
        const preRotateVertices = [
            // Front face
            [hl, -hh, hw], // ground
            [hl, -hh, -hw], // ground
            [hl, 0, -hw],
            [hl, hh, 0], // ridge end
            [hl, 0, hw],
            // Back face
            [-hl, -hh, hw], // ground
            [-hl, -hh, -hw], // ground
            [-hl, 0, -hw],
            [-hl, hh, 0], // ridge end
            [-hl, 0, hw],
        ];
        this.vertices = preRotateVertices.map(p => rotateAroundOrigin(p, Math.PI / 8, -Math.PI / 8, -0.14));
        this.faces = [
            [4, 3, 8, 9],  // near roof face
            [0, 4, 9, 5],  // near wall face
            [0, 1, 2, 3, 4],  // front face
        ];
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        let clr = this.baseColor;
        for (const face of this.faces) {
            let startVertex = this.vertices[face[0]];
            ctx.beginPath();
            ctx.moveTo(wFactor * (this.cX + startVertex[0]), hFactor * (this.cY - startVertex[1]));
            for (let v_idx = 1; v_idx < face.length; v_idx++) {
                let endVertex = this.vertices[face[v_idx]];
                ctx.lineTo(wFactor * (this.cX + endVertex[0]), hFactor * (this.cY - endVertex[1]));
                startVertex = endVertex;
            }
            ctx.closePath();
            ctx.fillStyle = clr;
            clr = shadeColor(clr, 30);
            ctx.strokeStyle = shadeColor(this.baseColor, 140);
            ctx.lineWidth = 2 * wFactor;
            ctx.fill();
            ctx.stroke();
        }
        ctx.restore();
    }
}
class Port {
    constructor(x, y, hexSideLen, orientation, porttype) {
        // 0 3:1, 1 brick, 2 grain, 3 lumber, 4 ore, 5 wool
        this.cX = x;
        this.cY = y;
        switch (porttype) {
            case 0:
                this.porttext = "Brick\n2:1"
                break;
            case 1:
                this.porttext = "Grain\n2:1"
                break;
            case 2:
                this.porttext = "Lumber\n2:1"
                break;
            case 3:
                this.porttext = "Ore\n2:1"
                break;
            case 4:
                this.porttext = "Wool\n2:1"
                break;
            case 5:
                this.porttext = "3:1";
                break;
            default:
                console.error("Invalid port type: " + porttype);
        }
        this.hexSideLen = hexSideLen;
        this.portAngle = 0;
        switch (orientation) {
            case 0:
                this.portAngle = Math.PI / 6;
                break;
            case 1:
                this.portAngle = -Math.PI / 6;
                break;
            case 2:
                this.portAngle = -Math.PI / 2;
                break;
            case 3:
                this.portAngle = -Math.PI * 5 / 6;
                break;
            case 4:
                this.portAngle = Math.PI * 5 / 6;
                break;
            case 5:
                this.portAngle = Math.PI / 2;
                break;
        }
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        // Draw port docks, at appropriate orientation
        ctx.translate(this.cX*wFactor, this.cY*hFactor);
        ctx.rotate(-this.portAngle);
        ctx.drawImage(PORT_DOCKS,
            -this.hexSideLen / 2*wFactor,
            -this.hexSideLen*hFactor, 
            this.hexSideLen*wFactor,
            this.hexSideLen*hFactor);
        ctx.rotate(this.portAngle);
        ctx.translate(-this.cX*wFactor, -this.cY*hFactor);
        ctx.restore();  // redundant measure to avoid translation/rotation error

        ctx.save();
        const portShipSize = this.hexSideLen * 1.1;
        const shipPos = rotateAroundOrigin([0,this.hexSideLen,0], 0, 0, this.portAngle);
        // Draw ship at port
        ctx.drawImage(PORT_SHIP, 
            wFactor * (this.cX+shipPos[0]-portShipSize*0.5), 
            hFactor * (this.cY - shipPos[1]-portShipSize*0.5), 
            wFactor*portShipSize, wFactor*portShipSize
        );
        // Draw port text
        ctx.font = `bold ${20 * wFactor}px Arial`;
        ctx.fillStyle = 'black';
        ctx.textAlign = 'center';
        const lines = this.porttext.split('\n');
        ctx.textBaseline = (lines.length > 1) ? 'bottom':'middle';
        for (var i = 0; i < lines.length; i++) {
            ctx.fillText(lines[i], 
                wFactor * (this.cX+shipPos[0]),
                hFactor * (this.cY - shipPos[1]-portShipSize*0.14));
            ctx.textBaseline = 'top';
        }

        ctx.restore();
    }
}
// TODO: currently shows all dev cards all the time; add mode to show only owned cards & stack, like real game

class Road {
    constructor(x, y, orientation, baseColor) {
        this.cX = x;
        this.cY = y;
        this.baseColor = baseColor;
        const hl = DRAWING_SCALE * 1.65;
        const hw = DRAWING_SCALE * 0.3;
        const hh = DRAWING_SCALE * 0.3;
        const preRotateVertices = [
            // Front face
            [hl, -hh, hw], // ground
            [hl, -hh, -hw], // ground
            [hl, hh, -hw],
            [hl, hh, hw],
            // Back face
            [-hl, -hh, hw], // ground
            [-hl, -hh, -hw], // ground
            [-hl, hh, -hw],
            [-hl, hh, hw],
        ];
        let xangle = Math.PI / 8;
        let yangle = -Math.PI / 8;
        let zangle = 0;
        switch (orientation) {
            case 0:
            case 3:
                this.faceorder = [0, 1, 2];  // lightest to darkest, for rendering
                zangle = Math.PI / 6;
                break;
            case 1:
            case 4:
                this.faceorder = [1, 0, 2];
                zangle = -Math.PI / 6;
                break;
            case 2:
            case 5:
                this.faceorder = [1, 2, 0];
                xangle = Math.PI * 3 / 8;
                zangle = Math.PI / 2;
                break;
        }
        this.vertices = preRotateVertices.map(p => rotateAroundOrigin(p, xangle, yangle, zangle));
        this.faces = [
            [2, 3, 7, 6],  // top face
            [0, 3, 7, 4],  // near wall face
            [0, 1, 2, 3],  // front face (road end)
        ];
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        let faceidx = 0;
        for (const face of this.faces) {
            let startVertex = this.vertices[face[0]];
            ctx.beginPath();
            ctx.moveTo(wFactor * (this.cX + startVertex[0]), hFactor * (this.cY - startVertex[1]));
            for (let v_idx = 1; v_idx < face.length; v_idx++) {
                let endVertex = this.vertices[face[v_idx]];
                ctx.lineTo(wFactor * (this.cX + endVertex[0]), hFactor * (this.cY - endVertex[1]));
                startVertex = endVertex;
            }
            ctx.closePath();
            ctx.fillStyle = shadeColor(this.baseColor, 25 * this.faceorder[faceidx]);
            ctx.strokeStyle = shadeColor(this.baseColor, 140);
            ctx.lineWidth = 2 * wFactor;
            ctx.fill();
            ctx.stroke();
            faceidx++;
        }
        ctx.restore();
    }
}
class Robber {
    constructor(x, y) {
        this.cX = x - 50;
        this.cY = y - 15;
        this.hr = DRAWING_SCALE*0.9;
        this.r = DRAWING_SCALE*1.1;
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        ctx.fillStyle = "grey";
        ctx.strokeStyle = "black";
        // Shadow, to give depth illusion
        ctx.shadowColor = 'black';
        ctx.shadowBlur = 5 * wFactor;
        ctx.shadowOffsetX = 2 * wFactor;
        ctx.shadowOffsetY = 2 * hFactor;
        ctx.beginPath();

        // Draw oval base
        ctx.beginPath();
        ctx.ellipse(this.cX * wFactor, (this.cY + 1.5 * this.r) * hFactor, this.r * wFactor, (0.4 * this.r) * hFactor, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.lineWidth = 2 * wFactor;
        ctx.stroke();

        // Draw oval body
        ctx.beginPath();
        ctx.ellipse(this.cX * wFactor, this.cY * hFactor, this.r * wFactor, (1.5 * this.r) * hFactor, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.lineWidth = 2 * wFactor;
        ctx.stroke();

        // Draw circle head
        ctx.beginPath();
        ctx.arc(this.cX * wFactor, (this.cY - 1.5 * this.hr) * hFactor, this.hr * wFactor, 0, Math.PI * 2);
        ctx.fill();
        ctx.lineWidth = 2 * wFactor;
        ctx.stroke();

        ctx.restore();
    }
}
class Img {
    constructor(x, y, width, height, image) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.image = image;
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        if (this.image !== undefined) {
            ctx.drawImage(this.image, this.x * wFactor, this.y * hFactor, this.width * wFactor, this.height * hFactor);
        }
        ctx.restore();
    }
}
class PlayerHand {
    // Reused for bank display
    constructor(x, y, height, color, LA, LR, vps, resource_arr, dev_arr, nKnightsPlayed, id) {
        this.x = x;
        this.y = y;
        this.height = height;
        this.width = height*1.4;
        this.color = color;
        this.cW = this.width*0.16;
        this.nK = nKnightsPlayed;
        this.cards = resource_arr;
        this.dCards = dev_arr;
        this.cardStacks = [];
        this.id = id;
        let cXOffset = this.width*0.03;
        Object.keys(RES_NAMES).forEach((key, idx) => {
            this.cardStacks[this.cardStacks.length] = new CardStack(
                this.x + cXOffset,
                this.y + this.cW*0.2,
                this.cW, HEX_IMAGES[key], RES_NAMES[key], this.cards[idx],
                true
            );
            cXOffset += this.width*0.14; // 0.19 for even spacing
        });
        
        this.dCardStacks = [];
        cXOffset = this.width*0.03;
        Object.keys(DEV_NAMES).forEach((key, idx) => {
            this.dCardStacks[this.dCardStacks.length] = new CardStack(
                this.x + cXOffset,
                this.y + this.cW*2,
                this.cW, DEV_IMAGES[key], DEV_NAMES[key], this.dCards[idx],
                vps===0  // only show empty dev card stacks if bank
            );
            cXOffset += this.width*0.14;
        });
        // Longest road and largest army
        this.LA = LA;
        this.LR = LR;
        this.vp_cards = [];
        let vpcy = this.y + this.cW*0.2;
        if(this.LA) {
            this.vp_cards[this.vp_cards.length] = new ResourceCard(
                this.x + this.width - this.cW*1.2,
                vpcy,
                this.cW, LRGST_ARMY_IMG, "Largest\nArmy");
            vpcy = this.y + this.cW*2;
        } 
        if(this.LR) {
            this.vp_cards[this.vp_cards.length] = new ResourceCard(
                this.x + this.width - this.cW*1.2,
                vpcy,
                this.cW, LNGST_ROAD_IMG, "Longest\nRoad");
        }
        this.vps = vps;
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        ctx.beginPath();
        ctx.fillStyle = shadeColor(this.color, 30);
        ctx.rect(this.x*wFactor, this.y*hFactor, this.width*wFactor, this.height*hFactor);
        ctx.lineWidth = 3*wFactor;
        ctx.fill();
        ctx.strokeStyle = shadeColor(this.color, 150);
        ctx.stroke();
        ctx.restore();
        
        this.cardStacks.forEach((cStack) => {cStack.draw(ctx, wFactor, hFactor); });
        this.dCardStacks.forEach((cStack) => {cStack.draw(ctx, wFactor, hFactor); });
        this.vp_cards.forEach((card) => {card.draw(ctx, wFactor, hFactor); });
        if(this.vps > 0) {
            ctx.font = `bold ${DRAWING_SCALE * 1.2 * wFactor}px Arial`;
            ctx.fillStyle = 'black';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            if(this.nK > 0) {
                ctx.fillText(`P${this.id}  ${this.vps} VP   ${this.nK} K`, wFactor * (this.x+DRAWING_SCALE*0.3), hFactor * (this.y + this.height));
            } else {
                ctx.fillText(`P${this.id}  ${this.vps} VP`, wFactor * (this.x+DRAWING_SCALE*0.3), hFactor * (this.y + this.height));
            }
        } else {
            // TODO: find better way of indicating current player in bank
            ctx.font = `bold ${DRAWING_SCALE * 1.2 * wFactor}px Arial`;
            ctx.fillStyle = 'black';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            ctx.fillText(`Current Player: ${brd_s_o["curr_turn"]}`, wFactor * (this.x+DRAWING_SCALE*0.3),
                hFactor * (this.y + this.height));
        }
    }
}
class CardStack {
    constructor(x, y, cardW, image, text, n, indicate_empty) {
        this.x = x;
        this.y = y;
        this.cW = cardW;
        this.cH = cardW*1.6;
        this.image = image;
        this.cText = text;
        this.n = n;
        this.indicate_empty = indicate_empty;
        this.offset = cardW*0.03;
        this.cards = [];
        this.nShown = Math.min(this.n, 5);
        for(let i = 0; i < this.nShown-1; i++) {
            this.cards[this.cards.length] = new ResourceCard(
                this.x + i*this.offset,
                this.y + i*this.offset,
                this.cW, undefined, "");
        }
        this.topCard = new ResourceCard(
                this.x + (this.nShown-1)*this.offset,
                this.y + (this.nShown-1)*this.offset,
                this.cW, this.image, this.cText);
    }
    draw(ctx, wFactor, hFactor) {
        this.cards.forEach((stackedCard) => {
            stackedCard.draw(ctx, wFactor, hFactor); 
        });
        if(this.n > 0) {
            this.topCard.draw(ctx, wFactor, hFactor);
        } 
        else if(this.indicate_empty) {
            ctx.save();
            ctx.beginPath();
            ctx.fillStyle = "#aaaaaa44";
            ctx.rect(this.x*wFactor, this.y*hFactor, this.cW*wFactor, this.cH*hFactor);
            ctx.lineWidth = wFactor;
            ctx.fill();
            ctx.strokeStyle = "#33333344";
            ctx.stroke();
        }
            
        
        // Show number of cards in stack
        if(this.n > 1) {
            ctx.save();
            ctx.beginPath();
            const radius = wFactor*this.cW*0.15;
            // Base token
            ctx.arc(this.x*wFactor, this.y*hFactor, radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = 'white';
            ctx.fill();
            ctx.closePath();
            ctx.restore();
            ctx.save();
            // Number of cards
            ctx.font = `bold ${this.cW*0.2*wFactor}px Arial`;
            ctx.fillStyle = 'black';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(this.n, this.x*wFactor, this.y*hFactor);
            ctx.restore();
        }
    }
}
class ResourceCard {
    constructor(x, y, width, image, text) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = this.width*1.6;
        this.image = image;
        this.cardColor = "#eace9c";
        this.text = text;
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        ctx.beginPath();
        ctx.fillStyle = this.cardColor;
        ctx.rect(this.x*wFactor, this.y*hFactor, this.width*wFactor, this.height*hFactor);
        ctx.lineWidth = wFactor;
        ctx.fill();
        ctx.strokeStyle = shadeColor(this.cardColor, 60);
        ctx.stroke();
        if (this.image !== undefined) {
            ctx.drawImage(this.image, this.x * wFactor, (this.y+3) * hFactor, (this.width-1) * wFactor, (this.width-1) * wFactor);
        }
        // Write resource name
        ctx.font = `bold ${this.width*0.21*wFactor}px Arial`;
        ctx.fillStyle = 'black';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';

        const lines = this.text.split('\n');
        for (var i = 0; i < lines.length; i++) {
            ctx.fillText(lines[i], (this.x+this.width/2)*wFactor, (this.y+1.35*this.width)*hFactor);
            ctx.textBaseline = 'top';
        }
        // NOTE: assumes that there are at most two lines of text
        ctx.restore();
    }
}
class Dice {
    constructor(cX, cY, width, val1, val2) {
        this.x = cX-width*1.1;
        this.y = cY-width/2; 
        this.width = width;
        this.v1 = val1;
        this.v2 = val2;
    }
    draw(ctx, wFactor, hFactor) {
        const dotR = wFactor*this.width / 10; // dot radius
        function drawDot(x, y) {
            ctx.beginPath();
            ctx.arc(x, y, dotR, 0, Math.PI * 2);
            ctx.fill();
            ctx.closePath();
        }
        function drawDots(dv, w, x, y) {
            const closeLoc = w*0.25;
            const farLoc = w*0.75;

            // Draw dots based on the dice value
            if (dv === 1 || dv === 3 || dv === 5) {
                drawDot(x+w / 2, y+w / 2); // Center dot
            }
            if (dv >= 2) {
                drawDot(x+closeLoc, y+closeLoc); // Top left
                drawDot(x+farLoc, y+farLoc); // Bottom right
            }
            if (dv >= 4) {
                drawDot(x+farLoc, y+closeLoc); // Top right
                drawDot(x+closeLoc, y+farLoc); // Bottom left
            }
            if (dv === 6) {
                drawDot(x+closeLoc, y+w / 2); // Middle left
                drawDot(x+farLoc, y+w / 2); // Middle right
            }
        }
        const sx = this.x*wFactor; // scaled x
        const sy = this.y*wFactor; // scaled y
        const wd = this.width*wFactor;
        ctx.beginPath();
        ctx.fillStyle = "yellow";
        ctx.rect(sx, sy, wd, wd);
        ctx.fill();
        ctx.lineWidth = wFactor;
        ctx.stroke();
        ctx.fillStyle = "red";
        drawDots(this.v1, wd, sx, sy);

        ctx.beginPath();
        ctx.fillStyle = "red";
        ctx.rect(sx+this.width*1.2*wFactor, sy, wd, wd);
        ctx.lineWidth = wFactor;
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = "yellow";
        drawDots(this.v2, wd, sx+this.width*1.2*wFactor, sy);
    }
}
/* --------------------- UTILITY FUNCTIONS --------------------- */
/*
    * Darkens/brightens given color, in hex format '#XXXXXX'
    */
function shadeColor(color, shadeval) {
    color = color.substring(1);
    let rgb = [
        Math.min(255, Math.max(0, parseInt(color.substring(0, 2), 16) - shadeval)).toString(16),
        Math.min(255, Math.max(0, parseInt(color.substring(2, 4), 16) - shadeval)).toString(16),
        Math.min(255, Math.max(0, parseInt(color.substring(4, 6), 16) - shadeval)).toString(16),
    ];
    let shadedColor = "#";
    rgb.forEach((element) => {
        shadedColor += (element.length === 1) ? '0' + element : element;
    });
    return shadedColor;
}
/*
    * Rotates given 3D point in format [x,y,z] around the origin by given 
    * angles
    */
function rotateAroundOrigin(pointArr, angleX, angleY, angleZ) {
    // Non zero rotation matrix values
    const cosX = Math.cos(angleX);
    const sinX = Math.sin(angleX);
    const cosY = Math.cos(angleY);
    const sinY = Math.sin(angleY);
    const cosZ = Math.cos(angleZ);
    const sinZ = Math.sin(angleZ);

    const [x, y, z] = pointArr; // unpack array

    // Rotate around x-axis
    let tempY = cosX * y - sinX * z;
    let tempZ = sinX * y + cosX * z;
    // Rotate around y-axis
    let tempX = cosY * x + sinY * tempZ;
    tempZ = -sinY * x + cosY * tempZ;
    // Rotate around z-axis
    const newX = cosZ * tempX - sinZ * tempY;
    const newY = sinZ * tempX + cosZ * tempY;
    return [newX, newY, tempZ];
}
/* 
  * Tile idx placement:
  *    18 17 16
  *   15 14 13 12      
  * 11 10  9  8  7
  *   6  5  4  3
  *    2  1  0 
*/
function hex_center_x(hexW, cX, idx) {
    if (idx > 15) {
        return cX + hexW * (RLENS[4] / 2 - idx + 16 - 0.5);
    } else if (idx > 11) {
        return cX + hexW * (RLENS[3] / 2 - idx + 12 - 0.5);
    } else if (idx > 6) {
        return cX + hexW * (RLENS[2] / 2 - idx + 7 - 0.5);
    } else if (idx > 2) {
        return cX + hexW * (RLENS[1] / 2 - idx + 3 - 0.5);
    } else {
        return cX + hexW * (RLENS[0] / 2 - idx - 0.5);
    }
}
function hex_center_y(tileH, cY, idx) {
    const rowH = tileH * 0.75;
    if (idx > 15) {
        // Top row
        return cY - rowH * 2;
    } else if (idx > 11) {
        return cY - rowH;
    } else if (idx > 6) {
        return cY;
    } else if (idx > 2) {
        return cY + rowH;
    } else {
        return cY + rowH * 2;
    }
}
/*
    * Obtain coordinates of hexagon corner, defined by index: 
    *    1 
    * 0     2
    * 
    * 5     3
    *    4
    */
function hex_corner_x(hexW, hexCX, idx) {
    switch (idx) {
        case 0:
        case 5:
            return hexCX - hexW / 2;
        case 1:
        case 4:
            return hexCX;
        default:
            return hexCX + hexW / 2;
    }
}
function hex_corner_y(tileH, hexCY, idx) {
    switch (idx) {
        case 1:
            return hexCY - tileH / 2;
        case 4:
            return hexCY + tileH / 2;
        case 0:
        case 2:
            return hexCY - tileH / 4;
        default:
            return hexCY + tileH / 4;
    }
}
/*
    * Obtain coordinates of center of hexagonal sides, based on index:
    *        .        0 upper left, increasing clockwise
    *    0       1
    * .             .
    *
    * 5             2
    *
    * .             .
    *    4       3
    *        .
    */
function hex_side_x(hexW, hexCX, idx) {
    switch (idx) {
        case 5:
            return hexCX - hexW / 2;
        case 2:
            return hexCX + hexW / 2;
        case 0:
        case 4:
            return hexCX - hexW / 4;
        default:
            return hexCX + hexW / 4;
    }
}
function hex_side_y(tileH, hexCY, idx) {
    switch (idx) {
        case 0:
        case 1:
            return hexCY - tileH * 3 / 8;
        case 5:
        case 2:
            return hexCY;
        default:
            return hexCY + tileH * 3 / 8;
    }
}
function hex_port_x(hexW, hexCX, idx) {
    switch (idx) {
        case 5:
            return hexCX - hexW;
        case 2:
            return hexCX + hexW;
        case 0:
        case 4:
            return hexCX - hexW / 2;
        default:
            return hexCX + hexW / 2;
    }
}
function hex_port_y(tileH, hexCY, idx) {
    switch (idx) {
        case 0:
        case 1:
            return hexCY - tileH * 3 / 4;
        case 5:
        case 2:
            return hexCY;
        default:
            return hexCY + tileH * 3 / 4;
    }
}
function gen_socket_listeners(socket) {
    socket.onopen = (event) => {
        console.log(`Connected to ws server; event:${event}`);
        // socket.send(JSON.stringify({"type": "ping"}))
    };
    socket.onclose = (event) => {
        if (event.wasClean) {
            console.log(`Closed ws connection; code:${event.code}, reason:${event.reason}`);
        } else {
            console.log("Connection abruptly closed.");
            console.log(event);
        }
        // clearInterval(pingInterval);
        if (initialized_board) { // only show lost connection if board was initialized
            let lostconnectDiv = document.getElementById("lostconnect_div");
            lostconnectDiv.style.display = 'block';
        }
    };
    socket.onerror = (error) => {
        console.error("WebSocket error: ", error);
    };

    socket.onmessage = (event) => {
        let data = JSON.parse(event.data);
        switch(data.type) {
            case "pong":
                console.log("Received pong.");
                // On first pong, request initial board state
                if (!initialized_board) {
                    console.log("requesting newly initialized board");
                    socket.send(JSON.stringify({"type": "new_board_request"}));
                    initialized_board = true;
                }
                break;
            case "new_board":
                // Once connected, hide loading animation
                console.log("Received new board.");
                initialized_board = true;
                Object.keys(data).forEach((key) => {
                    if (key in brd_s_o) {
                        brd_s_o[key] = data[key];
                        // console.log(key, data[key]);
                    }
                });
                let loadingDiv = document.getElementById("loading_div");
                loadingDiv.style.display = 'none';
                gameBoard.reinit();
                gameBoard.draw();
                break;
            case "board_update":
                let true_update = false;
                Object.keys(data).forEach((key) => {
                    if (key in brd_s_o) {
                        brd_s_o[key] = data[key];
                        true_update = true;
                    }
                });
                if (true_update) {
                    console.log("Updated board state. Redrawing.");
                    gameBoard.clearComponents();
                    gameBoard.addComponents();
                    gameBoard.draw();
                }
                break;
            case "notif":
                if (data.message === "human_turn") {
                    if (data.game_cycle_status === 1) {
                        showModal("Please place the robber.");
                        gameBoard.active_action = "robber_btn";
                        gameBoard.draw();
                    } else if (data.game_cycle_status === 2 || data.game_cycle_status === 3) {
                        showModal("Please place a road.");
                        gameBoard.active_action = "road_btn";
                        gameBoard.draw();
                    }
                    console.log("It's your turn!");
                } else if (data.message === "game_over") {
                    console.log("Player" + data.pidx + " won!");
                    showModal("Player " + data.pidx + " won!");
                } else if (data.message === "invalid_action") {
                    showModal("Invalid action; please try again. It is still your turn.");
                } else if (data.message === "saved_game") {
                    showModal("Successfully saved game to <span class=\"monospace\">" + data.filename + "</span>");
                } else if (data.message === "step_game_replay") {
                    console.log("Replaying saved game");
                } else if (data.message === "invalid_act_during_replay") {
                    showModal("Currently replaying saved game; please hit End Turn to step through game history.");
                } else {
                    console.log("Received notification: " + data.message);
                }
                // TODO: give actual notification
                break;
            default:
                console.error("Invalid message type: ", data.type);
        }
    };
    /*
    const pingInterval = setInterval(function () {
        socket.send(JSON.stringify({"type": "ping"}))
    }, PING_INTERVAL*1000);
    */
    window.addEventListener("click", function(e) {
        mouse.x = e.x;
        mouse.y = e.y;
        let gameX = mouse.x*gameBoard.wrFactor;
        let gameY = mouse.y*gameBoard.hrFactor;

        let modal = document.getElementById("myModal");
        if (e.target === modal) {
            closeModal();
            return;
        }
        // TODO: register action clicks & send action to server
        if(e.target.classList.contains('act_button')) {
            let action = e.target.id;
            console.log("Clicked button: " + action);
            gameBoard.active_action = action;
            if(action === "end_turn_btn") {
                socket.send(JSON.stringify({"type": "action", "action": "end_turn_btn"}));
                // Reset active action
                gameBoard.active_action = "";
            } else if(action === "save_game_btn") {
                socket.send(JSON.stringify({"type": "action", "action": "save_game_btn"}));
                // Reset active action
                gameBoard.active_action = "";
            } else if(action === "reset_game_btn") {
                socket.send(JSON.stringify({"type": "action", "action": "reset_game_btn"}));
                // Reset active action
                gameBoard.active_action = "";
            } else if (action === "dev_card_btn") {
                socket.send(JSON.stringify({"type": "action", "action": "dev_card_btn"}));
                // Reset active action
                gameBoard.active_action = "";
            }
            gameBoard.draw();
        }
        if(gameBoard.active_action !== "") {
            let act = gameBoard.active_action;
            if (act === "city_btn") { act = "settlement_btn"; }
            let rad = 25;
            if (act === "robber_btn" || act === "trade_btn") {
                rad = 50;
            }
            console.log("Active action: " + gameBoard.active_action);
            // Iterate over hover list to find clicked item
            for(let i = 0; i < gameBoard.hoverLists[act].length; i++) {
                let item = gameBoard.hoverLists[act][i];
                if((gameX - item.x)**2 + (gameY - item.y)**2 < rad**2) {
                    console.log("Clicked " + item.id + " at " + item.r + ", " + item.c);
                    // Send websocket message to server, indicating human action
                    socket.send(JSON.stringify({
                        "type": "action",
                        "action": gameBoard.active_action,
                        "r": item.r,
                        "c": item.c,
                    }));
                    // Reset active action
                    gameBoard.active_action = "";
                    // TODO: redraw?
                    break;
                }
            }
        }

    });
}

// --------------------- MODAL NOTIFICATIONS ---------------------
function openModal() {
    let modal = document.getElementById("myModal");
    let modal_paragraph = document.getElementById("modal_p_content");
    modal_paragraph.innerHTML = "You have lost connection to the server. Please refresh the page to reconnect.";
    modal.style.display = "block";
}
function showModal(message) {
    let modal = document.getElementById("myModal");
    let modal_paragraph = document.getElementById("modal_p_content");
    modal_paragraph.innerHTML = message;
    modal.style.display = "block";
}
function closeModal() {
    let modal = document.getElementById("myModal");
    modal.style.display = "none";
    // treated as affirmative response to modal no matter what
}

function acknowledgeModal() {
    closeModal();
}
