 const GRID_SIZE = 20;
        const INITIAL_SPEED = 200;
        
        let gameBoard;
        let snake = [];
        let food = {};
        let direction = { x: 1, y: 0 };
        let gameRunning = false;
        let score = 0;
        let highScore = parseInt(localStorage.getItem('snakeHighScore') || '0');
        let level = 1;
        let gameSpeed = INITIAL_SPEED;
        let gameLoop;
        
        // Elementos del DOM
        const gameBoardElement = document.getElementById('gameBoard');
        const scoreElement = document.getElementById('score');
        const highScoreElement = document.getElementById('highScore');
        const levelElement = document.getElementById('level');
        const gameOverScreen = document.getElementById('gameOver');
        const finalScoreElement = document.getElementById('finalScore');
        const newRecordElement = document.getElementById('newRecord');
        const startScreen = document.getElementById('startScreen');
        
        // Inicializar juego
        function initGame() {
            // Crear tablero
            gameBoardElement.innerHTML = '';
            for (let i = 0; i < GRID_SIZE * GRID_SIZE; i++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                gameBoardElement.appendChild(cell);
            }
            
            // Mostrar récord actual
            highScoreElement.textContent = highScore;
            
            // Inicializar serpiente en el centro del tablero
            snake = [
                { x: 10, y: 10 },
                { x: 9, y: 10 },
                { x: 8, y: 10 }
            ];
            
            // Generar primera comida
            spawnFood();
            
            // Renderizar
            render();
        }
        
        function startGame() {
            startScreen.style.display = 'none';
            gameRunning = true;
            score = 0;
            level = 1;
            gameSpeed = INITIAL_SPEED;
            direction = { x: 1, y: 0 };
            scoreElement.textContent = score;
            levelElement.textContent = level;
            
            // Reinicializar serpiente en posición segura
            snake = [
                { x: 10, y: 10 },
                { x: 9, y: 10 },
                { x: 8, y: 10 }
            ];
            
            initGame();
            gameLoop = setInterval(update, gameSpeed);
        }
        
        function spawnFood() {
            let attempts = 0;
            do {
                food = {
                    x: Math.floor(Math.random() * GRID_SIZE),
                    y: Math.floor(Math.random() * GRID_SIZE)
                };
                attempts++;
                // Evitar bucle infinito si el tablero está muy lleno
                if (attempts > 100) break;
            } while (snake.some(segment => segment.x === food.x && segment.y === food.y));
            
            // Asegurar que la comida esté dentro del tablero
            food.x = Math.max(0, Math.min(GRID_SIZE - 1, food.x));
            food.y = Math.max(0, Math.min(GRID_SIZE - 1, food.y));
        }
        
        function update() {
            if (!gameRunning) return;
            
            // Mover cabeza
            const head = { ...snake[0] };
            head.x += direction.x;
            head.y += direction.y;
            
            // Verificar colisiones con paredes
            if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
                endGame();
                return;
            }
            
            // Verificar colisión consigo mismo
            if (snake.some(segment => segment.x === head.x && segment.y === head.y)) {
                endGame();
                return;
            }
            
            snake.unshift(head);
            
            // Verificar si comió
            if (head.x === food.x && head.y === food.y) {
                score++;
                scoreElement.textContent = score;
                
                // Crear partículas de celebración
                createParticles(head.x, head.y);
                
                // Aumentar nivel cada 5 llaves
                if (score % 5 === 0) {
                    level++;
                    levelElement.textContent = level;
                    gameSpeed = Math.max(70, INITIAL_SPEED - (level - 1) * 25);
                    clearInterval(gameLoop);
                    gameLoop = setInterval(update, gameSpeed);
                }
                
                // Generar nueva comida
                spawnFood();
                
                // NO remover el último segmento cuando come
            } else {
                // Solo remover el último segmento si NO comió
                snake.pop();
            }
            
            render();
        }
        
        function render() {
            const cells = gameBoardElement.children;
            
            // Limpiar tablero
            for (let cell of cells) {
                cell.innerHTML = '';
                cell.className = 'cell';
            }
            
            // Dibujar serpiente (solo segmentos válidos)
            snake.forEach((segment, index) => {
                if (segment.x >= 0 && segment.x < GRID_SIZE && segment.y >= 0 && segment.y < GRID_SIZE) {
                    const cellIndex = segment.y * GRID_SIZE + segment.x;
                    if (cellIndex >= 0 && cellIndex < cells.length) {
                        const cell = cells[cellIndex];
                        const segmentElement = document.createElement('div');
                        segmentElement.className = index === 0 ? 'snake-segment snake-head' : 'snake-segment';
                        cell.appendChild(segmentElement);
                    }
                }
            });
            
            // Dibujar comida (solo si está en posición válida)
            if (food.x >= 0 && food.x < GRID_SIZE && food.y >= 0 && food.y < GRID_SIZE) {
                const foodCellIndex = food.y * GRID_SIZE + food.x;
                if (foodCellIndex >= 0 && foodCellIndex < cells.length) {
                    const foodCell = cells[foodCellIndex];
                    const foodElement = document.createElement('div');
                    foodElement.className = 'food';
                    foodCell.appendChild(foodElement);
                }
            }
        }
        
        function createParticles(x, y) {
            const cellIndex = y * GRID_SIZE + x;
            const cell = gameBoardElement.children[cellIndex];
            const rect = cell.getBoundingClientRect();
            const containerRect = gameBoardElement.getBoundingClientRect();
            
            for (let i = 0; i < 8; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = (rect.left - containerRect.left + 15) + 'px';
                particle.style.top = (rect.top - containerRect.top + 15) + 'px';
                particle.style.transform = `rotate(${Math.random() * 360}deg)`;
                
                gameBoardElement.appendChild(particle);
                
                setTimeout(() => {
                    if (particle.parentNode) {
                        particle.remove();
                    }
                }, 800);
            }
        }
        
        function endGame() {
            gameRunning = false;
            clearInterval(gameLoop);
            
            finalScoreElement.textContent = score;
            
            // Verificar nuevo récord
            if (score > highScore) {
                highScore = score;
                localStorage.setItem('snakeHighScore', highScore.toString());
                highScoreElement.textContent = highScore;
                newRecordElement.style.display = 'block';
            } else {
                newRecordElement.style.display = 'none';
            }
            
            gameOverScreen.style.display = 'block';
        }
        
        function restartGame() {
            gameOverScreen.style.display = 'none';
            startGame();
        }
        
        // Controles
        document.addEventListener('keydown', (e) => {
            if (!gameRunning) return;
            
            const keyMap = {
                'ArrowUp': { x: 0, y: -1 },
                'ArrowDown': { x: 0, y: 1 },
                'ArrowLeft': { x: -1, y: 0 },
                'ArrowRight': { x: 1, y: 0 },
                'KeyW': { x: 0, y: -1 },
                'KeyS': { x: 0, y: 1 },
                'KeyA': { x: -1, y: 0 },
                'KeyD': { x: 1, y: 0 }
            };
            
            const newDirection = keyMap[e.code];
            if (newDirection) {
                // Evitar que la serpiente se mueva hacia atrás
                if (newDirection.x !== -direction.x || newDirection.y !== -direction.y) {
                    direction = newDirection;
                }
                e.preventDefault();
            }
        });
        
        // Inicializar al cargar
        initGame();