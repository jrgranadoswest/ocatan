// HTML canvas frontend to display games
// Certain elements may be poorly designed/structured, but this just needs to 
// take some board representation & display it
/* --------------------- CONSTANTS & GLOBALS --------------------- */
const TOKEN_RATIO = 1 / 16;  // ratio of chance token size to board size
const BORDER_RATIO = 0.07; // ratio of border to board size
// Number of dots shown for each dice sum 
//                   2  3  4  5  6     8  9  10 11 12
const CHANCE_DOTS = [1, 2, 3, 4, 5, 0, 5, 4, 3, 2, 1];
const RLENS = [3, 4, 5, 4, 3];  // row lengths
let canvas;
let ctx;
let gameBoard;

// Load images
const DESERT_IMG = new Image();
DESERT_IMG.src = './static/img/desert_hex.png';
const PASTURE_IMG = new Image();
PASTURE_IMG.src = './static/img/pasture_hex.png';
const FOREST_IMG = new Image();
FOREST_IMG.src = './static/img/forest_hex.png';
const FIELD_IMG = new Image();
FIELD_IMG.src = './static/img/wheat_hex.png';
const BRICK_IMG = new Image();
BRICK_IMG.src = './static/img/brick_hex.png';
const MOUNTAIN_IMG = new Image();
MOUNTAIN_IMG.src = './static/img/mountains_hex.png';
/*
    * Desert 'D'
    * Pasture (Wool) 'P'
    * Forest (Lumber) 'F'
    * Field (Grain) 'G'
    * Brick 'B'
    * Mountain (Ore) 'M'
    */
const HEX_IMAGES = {
    "B": BRICK_IMG,
    "D": DESERT_IMG,
    "G": FIELD_IMG,
    "F": FOREST_IMG,
    "M": MOUNTAIN_IMG,
    "P": PASTURE_IMG,
};
const COLORS = ["#00ffff", "#ffa500", "#a500ff", "#00ffa5"];

// Board state representation (currently static, filled with arbitrary board)
const BRD_HEX_STATE = "PGBPGMFMFDFGBPBGFPM";
// hex codes for different chance values, 0 means no token (desert)
const BRD_CHANCE_TKN_STATE = "B655438830B9A46C92A";
// orientation values for ports at each hex idx, 6 means no port
const BRD_PORT_ORIENT_S = "6343665266661665610";
// port types for port at each hex idx, 6: no port
const BRD_PORT_TYPE_S = "6005661066664663620";
const ROBBER_LOC = 9;
// Roads: 2 digit number tile, number indicating side, number indicating color
const BRD_RD_S = "00200010010101511432142214121302165209520942093206020633025307030713140018201111";
// Cities & settlements: 2 digit number tile, number: corner, number: color
const BRD_CITY_S = "003001110151061206331400";
const BRD_SET_S = "0010090214220932070307231111";


/* --------------------- Main Display Logic --------------------- */
// window.onload waits for whole page to load before running; as opposed to 
// document.onload which waits for DOM to be ready
window.onload = function () {
    canvas = document.getElementById("canvas1");
    // Construct square of maximum size
    if (window.innerWidth < window.innerHeight) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerWidth;
    } else {
        canvas.width = window.innerHeight;
        canvas.height = window.innerHeight;
    }
    gameBoard = new GameBoard(canvas, 1000, 1000);  // arbitrary vals
    gameBoard.resize();
}
window.addEventListener('resize', function () {
    gameBoard.resize();
});

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
        this.hFactor = this.canvas.height / this.renderHeight;
        this.components = [];
        this.staticComps = [];
        this.borderWidth = Math.floor(this.renderWidth * BORDER_RATIO);  // err lower
        this.bodyWidth = this.renderWidth - this.borderWidth * 2;
        this.hexW = this.bodyWidth / 5;
        this.tileH = this.hexW * (2 / Math.sqrt(3));
        // Build board
        this.#addBoardComponents();
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
    }
    resize() {
        // Construct square of maximum size
        if (window.innerWidth < window.innerHeight) {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerWidth;
        } else {
            this.canvas.width = window.innerHeight;
            this.canvas.height = window.innerHeight;
        }
        // Set scaling factors to redraw game elements at proper size
        this.wFactor = this.canvas.width / this.renderWidth;
        this.hFactor = this.canvas.height / this.renderHeight;
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
    #addBoardComponents() {
        const rowH = this.tileH * 0.75;
        const tileSize = this.bodyWidth / 5;
        const cX = this.renderWidth / 2;
        const cY = this.renderHeight / 2;
        const tokenSize = this.bodyWidth * TOKEN_RATIO;
        let cti = 0; // current tile index

        /* 
              * Tile adding order:
              *    19 18 17
              *   16 15 14 13      
              * 12 11 10  9  8
              *   7  6  5  4
              *    3  2  1 
              */
        for (let y = 0; y < 5; y++) {
            for (let x = 0; x < RLENS[y]; x++) {
                let tileCX = cX + this.hexW * (RLENS[y] / 2 - x - 0.5);
                let tileCY = cY + rowH * (2 - y);
                this.addBoardComponent(
                    new Img(
                        tileCX - this.tileH / 2,
                        tileCY - this.tileH / 2,
                        this.tileH,
                        this.tileH,
                        HEX_IMAGES[BRD_HEX_STATE[cti]]));
                if (BRD_CHANCE_TKN_STATE[cti] != '0') {
                    this.addBoardComponent(
                        new ChanceToken(
                            tileCX - tokenSize / 2,
                            tileCY - tokenSize / 2,
                            tokenSize,
                            tokenSize,
                            parseInt(BRD_CHANCE_TKN_STATE[cti], 16),
                            true));
                }
                if (BRD_PORT_ORIENT_S[cti] != '6') {
                    let portside = parseInt(BRD_PORT_ORIENT_S[cti]);
                    let sx = hex_side_x(this.hexW, tileCX, portside);
                    let sy = hex_side_y(this.tileH, tileCY, portside);
                    this.addBoardComponent(
                        new Port(sx, sy, this.tileH / 2,
                            portside,
                            parseInt(BRD_PORT_TYPE_S[cti])));
                }
                cti++;
            }
        }
        let sx, sy;
        // Parse board state for roads
        for (let i = 0; i < BRD_RD_S.length; i += 4) {
            let tileIdx = parseInt(BRD_RD_S.substring(i, i + 2));
            let orient = parseInt(BRD_RD_S[i + 2]);
            let clr = COLORS[parseInt(BRD_RD_S[i + 3])];
            sx = hex_side_x(this.hexW, hex_center_x(this.hexW, this.renderWidth / 2, tileIdx), orient);
            sy = hex_side_y(this.tileH, hex_center_y(this.tileH, this.renderHeight / 2, tileIdx), orient);
            this.addComponent(new Road(sx, sy, orient, clr));
        }
        // Parse board state for cities
        for (let i = 0; i < BRD_CITY_S.length; i += 4) {
            let tileIdx = parseInt(BRD_CITY_S.substring(i, i + 2));
            let corner = parseInt(BRD_CITY_S[i + 2]);
            let clr = COLORS[parseInt(BRD_CITY_S[i + 3])];
            sx = hex_corner_x(this.hexW, hex_center_x(this.hexW, this.renderWidth / 2, tileIdx), corner);
            sy = hex_corner_y(this.tileH, hex_center_y(this.tileH, this.renderHeight / 2, tileIdx), corner);
            this.addComponent(new City(sx, sy, clr));
        }
        // Parse board state for settlements
        for (let i = 0; i < BRD_SET_S.length; i += 4) {
            let tileIdx = parseInt(BRD_SET_S.substring(i, i + 2));
            let corner = parseInt(BRD_SET_S[i + 2]);
            let clr = COLORS[parseInt(BRD_SET_S[i + 3])];
            sx = hex_corner_x(this.hexW, hex_center_x(this.hexW, this.renderWidth / 2, tileIdx), corner);
            sy = hex_corner_y(this.tileH, hex_center_y(this.tileH, this.renderHeight / 2, tileIdx), corner);
            this.addComponent(new Settlement(sx, sy, clr));
        }
        // Place robber
        this.addComponent(new Robber(
            hex_center_x(this.hexW, this.renderWidth / 2, ROBBER_LOC),
            hex_center_y(this.tileH, this.renderWidth / 2, ROBBER_LOC)));
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
        const fontSize = 36 * wFactor;
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.fillStyle = (this.dv == 6 || this.dv == 8) ? 'red' : 'black';
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
        this.baseColor = shadeColor(baseColor, -30);
        const scaleFactor = 16; // TODO: use proportion of board size
        const hl = scaleFactor * 1.2;
        const hw = scaleFactor;
        const bh = scaleFactor * 1.2; // base height
        const rh = scaleFactor * 0.9; // roof height
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
class Settlement {
    constructor(x, y, baseColor) {
        this.cX = x;
        this.cY = y;
        this.baseColor = baseColor;
        const scaleFactor = 16;
        const hl = scaleFactor * 1.1;
        const hw = scaleFactor;
        const hh = scaleFactor * 0.9;
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
        this.baseColor = "#664248";
        switch (porttype) {
            case 0:
                this.porttext = "3:1";
                break;
            case 1:
                this.porttext = "Brick 2:1"
                break;
            case 2:
                this.porttext = "Grain 2:1"
                break;
            case 3:
                this.porttext = "Lumber 2:1"
                break;
            case 4:
                this.porttext = "Ore 2:1"
                break;
            case 5:
                this.porttext = "Wool 2:1"
                break;
        }
        const hw = hexSideLen / 2; // land width
        const hiw = hexSideLen * 0.25; // inner width; between docks
        const hew = hexSideLen * 0.3;  // half end width
        const heiw = hexSideLen * 0.1;  // half end inner width (between dock ends)
        const dl = hexSideLen * 0.4; // dock length
        const preRotateVertices = [
            // dock 1
            [-hw, 0, 0],
            [-hiw, 0, 0],
            [-heiw, dl, 0],
            [-hew, dl, 0],
            // dock 2
            [hw, 0, 0],
            [hiw, 0, 0],
            [heiw, dl, 0],
            [hew, dl, 0],
            // text center
            [0, 1.5 * dl, 0],
        ];
        let zangle = 0.5;
        switch (orientation) {
            case 0:
                zangle = Math.PI / 6;
                break;
            case 1:
                zangle = -Math.PI / 6;
                break;
            case 2:
                zangle = -Math.PI / 2;
                break;
            case 3:
                zangle = -Math.PI * 5 / 6;
                break;
            case 4:
                zangle = Math.PI * 5 / 6;
                break;
            case 5:
                zangle = Math.PI / 2;
                break;
        }
        this.vertices = preRotateVertices.map(p => rotateAroundOrigin(p, 0, 0, zangle));
        this.faces = [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
        ];
    }
    draw(ctx, wFactor, hFactor) {
        ctx.save();
        // Draw two docks (each face is just one flatly-drawn dock
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
            ctx.fillStyle = this.baseColor;
            ctx.strokeStyle = shadeColor(this.baseColor, 60);
            ctx.lineWidth = 2 * wFactor;
            ctx.fill();
            ctx.stroke();
        }
        // Draw port text
        const fontSize = 24 * wFactor;
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.fillStyle = 'black';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.porttext, wFactor * (this.cX + this.vertices[8][0]), hFactor * (this.cY - this.vertices[8][1]));
        ctx.restore();
    }
}
class Road {
    constructor(x, y, orientation, baseColor) {
        this.cX = x;
        this.cY = y;
        this.baseColor = baseColor;
        const scaleFactor = 16;
        const hl = scaleFactor * 1.6;
        const hw = scaleFactor * 0.3;
        const hh = scaleFactor * 0.3;
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
        this.hr = 15;
        this.r = 20;
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

        // Draw circle head(?)
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
        shadedColor += (element.length == 1) ? '0' + element : element;
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

