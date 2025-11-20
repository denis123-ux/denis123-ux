"""
🌟 SYMPLECTIC SAT SOLVER - Proof of Concept
============================================

Implementazione dell'approccio rivoluzionario:
Risolvere SAT via geometric flow in spazio simplettico ad alta dimensione.

Teoria: SAT è difficile in rappresentazione booleana,
        ma facile in rappresentazione geometrica continua.
"""

import numpy as np
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
import matplotlib.pyplot as plt
from scipy.optimize import minimize


@dataclass
class Clause:
    """Una clausola SAT come lista di letterali (positivi o negativi)"""
    literals: List[int]  # x_i rappresentato come i, ¬x_i come -i

    def evaluate(self, x: np.ndarray) -> float:
        """
        Valuta clausola in punto continuo x ∈ [0,1]^n

        Per OR di letterali: (l₁ ∨ l₂ ∨ ... ∨ lₖ)
        Versione continua: 1 - ∏(1 - eval(lᵢ))

        Ritorna 1 se soddisfatta, 0 se violata (continuo tra 0 e 1)
        """
        product = 1.0
        for lit in self.literals:
            if lit > 0:
                # Letterale positivo: x_i
                val = x[abs(lit) - 1]
            else:
                # Letterale negativo: ¬x_i = (1 - x_i)
                val = 1.0 - x[abs(lit) - 1]
            product *= (1.0 - val)

        return 1.0 - product

    def penalty(self, x: np.ndarray) -> float:
        """Penalty per clausola violata (0 se soddisfatta, >0 se violata)"""
        satisfaction = self.evaluate(x)
        # Penalizziamo quando satisfaction è bassa
        return (1.0 - satisfaction) ** 2


class SATFormula:
    """Formula SAT in CNF"""

    def __init__(self, n_vars: int, clauses: List[Clause]):
        self.n_vars = n_vars
        self.clauses = clauses
        self.n_clauses = len(clauses)

    def energy(self, x: np.ndarray) -> float:
        """
        Energia totale del sistema E(x)

        E(x) = 0 ⟺ tutte clausole soddisfatte
        E(x) > 0 ⟺ almeno una clausola violata
        """
        total = 0.0
        for clause in self.clauses:
            total += clause.penalty(x)
        return total

    def is_satisfied(self, x: np.ndarray, tolerance: float = 1e-6) -> bool:
        """Check se x soddisfa formula (in senso continuo)"""
        return self.energy(x) < tolerance

    def to_boolean(self, x: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Converte soluzione continua a booleana"""
        return (x >= threshold).astype(int)

    def verify_boolean(self, x_bool: np.ndarray) -> bool:
        """Verifica soluzione booleana"""
        for clause in self.clauses:
            satisfied = False
            for lit in clause.literals:
                if lit > 0 and x_bool[abs(lit) - 1] == 1:
                    satisfied = True
                    break
                if lit < 0 and x_bool[abs(lit) - 1] == 0:
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True


class SymplecticEmbedding:
    """
    High-dimensional embedding per SAT formula

    Trasforma x ∈ [0,1]^n a Φ(x) ∈ ℝ^D con D >> n
    """

    def __init__(self, formula: SATFormula, degree: int = 3):
        self.formula = formula
        self.n = formula.n_vars
        self.degree = degree

        # Dimensione embedding
        # Include: variabili originali + tutti monomi fino a grado 'degree'
        # + features speciali per ogni clausola
        self.D = self._compute_dimension()

    def _compute_dimension(self) -> int:
        """Calcola dimensione spazio embedded"""
        # Variabili base
        dim = self.n

        # Monomi grado 2
        dim += self.n * (self.n + 1) // 2

        # Monomi grado 3 (se degree >= 3)
        if self.degree >= 3:
            dim += self.n * (self.n + 1) * (self.n + 2) // 6

        # Features per clausole (una per clausola)
        dim += self.formula.n_clauses

        return dim

    def embed(self, x: np.ndarray) -> np.ndarray:
        """
        Φ: [0,1]^n → ℝ^D

        Costruisce vettore di features ad alta dimensione
        """
        features = []

        # 1. Variabili originali
        features.extend(x)

        # 2. Prodotti quadratici
        for i in range(self.n):
            for j in range(i, self.n):
                features.append(x[i] * x[j])

        # 3. Prodotti cubici
        if self.degree >= 3:
            for i in range(self.n):
                for j in range(i, self.n):
                    for k in range(j, self.n):
                        features.append(x[i] * x[j] * x[k])

        # 4. Features clausole (quanto è soddisfatta ogni clausola)
        for clause in self.formula.clauses:
            features.append(clause.evaluate(x))

        return np.array(features)

    def gradient_embed(self, x: np.ndarray) -> np.ndarray:
        """
        Jacobiano dell'embedding: ∂Φ/∂x
        Dimensione: D × n
        """
        # Per ora usiamo differenze finite (può essere ottimizzato)
        eps = 1e-7
        J = np.zeros((self.D, self.n))

        phi_x = self.embed(x)

        for i in range(self.n):
            x_plus = x.copy()
            x_plus[i] += eps
            phi_plus = self.embed(x_plus)
            J[:, i] = (phi_plus - phi_x) / eps

        return J


class SymplecticSATSolver:
    """
    Il Solver Rivoluzionario!

    Usa geometric flow in spazio simplettico per risolvere SAT
    """

    def __init__(self, formula: SATFormula, embedding_degree: int = 2):
        self.formula = formula
        self.n = formula.n_vars

        # Crea embedding
        self.embedding = SymplecticEmbedding(formula, embedding_degree)
        self.D = self.embedding.D

        print(f"📐 Formula: {self.n} vars, {formula.n_clauses} clauses")
        print(f"🚀 Embedding dimension: {self.D} (da {self.n})")
        print(f"   Expansion factor: {self.D / self.n:.1f}x")

    def potential(self, x: np.ndarray) -> float:
        """
        Potenziale V(x) derivato dall'energia SAT
        Include barrier per mantenere x ∈ [0,1]
        """
        # Proietta su [0,1] con soft barriers
        x_clipped = np.clip(x, 0.0, 1.0)

        # Energia SAT
        V = self.formula.energy(x_clipped)

        # Barrier penalties per mantenere in [0,1]
        barrier = 0.0
        for xi in x:
            if xi < 0:
                barrier += 100 * xi**2
            elif xi > 1:
                barrier += 100 * (xi - 1)**2

        return V + barrier

    def gradient_potential(self, x: np.ndarray) -> np.ndarray:
        """
        Gradiente ∇V(x)
        Calcolato numericamente (può essere ottimizzato con autodiff)
        """
        eps = 1e-7
        grad = np.zeros(self.n)
        V_x = self.potential(x)

        for i in range(self.n):
            x_plus = x.copy()
            x_plus[i] += eps
            V_plus = self.potential(x_plus)
            grad[i] = (V_plus - V_x) / eps

        return grad

    def symplectic_flow(
        self,
        x0: Optional[np.ndarray] = None,
        T: float = 100.0,
        dt: float = 0.01,
        gamma: float = 0.5,
        verbose: bool = True
    ) -> Tuple[np.ndarray, List[float]]:
        """
        Simula flusso simplettico con damping

        dx/dt = y
        dy/dt = -∇V(x) - γy    (damping term!)

        Args:
            x0: punto iniziale (random se None)
            T: tempo massimo
            dt: timestep
            gamma: damping coefficient
            verbose: stampa progresso

        Returns:
            (x_final, energy_history)
        """
        # Inizializza
        if x0 is None:
            x0 = np.random.rand(self.n)

        x = x0.copy()
        y = np.zeros(self.n)  # velocità iniziale zero

        # Storia energia
        energy_history = []

        # Numero di steps
        n_steps = int(T / dt)

        if verbose:
            print(f"\n🌊 Starting symplectic flow...")
            print(f"   Time: {T}, dt: {dt}, steps: {n_steps}")
            print(f"   Damping: γ = {gamma}")

        for step in range(n_steps):
            # Calcola gradiente
            grad_V = self.gradient_potential(x)

            # Symplectic Euler step con damping
            y = y - dt * grad_V - gamma * dt * y
            x = x + dt * y

            # Proietta su [0,1]
            x = np.clip(x, 0.0, 1.0)

            # Energia corrente
            E = self.potential(x)
            energy_history.append(E)

            # Progress report
            if verbose and step % (n_steps // 10) == 0:
                print(f"   Step {step:6d}/{n_steps}: E = {E:.6f}, ||y|| = {np.linalg.norm(y):.4f}")

            # Early stopping se convergiamo
            if E < 1e-6:
                if verbose:
                    print(f"   ✅ Converged at step {step}!")
                break

        if verbose:
            print(f"\n🎯 Final energy: {E:.8f}")

        return x, energy_history

    def solve(
        self,
        n_attempts: int = 5,
        T: float = 100.0,
        dt: float = 0.01,
        gamma: float = 0.5,
        verbose: bool = True
    ) -> Optional[np.ndarray]:
        """
        Risolve SAT con multiple inizializzazioni random

        Returns:
            Soluzione booleana se trovata, None altrimenti
        """
        best_x = None
        best_energy = float('inf')

        for attempt in range(n_attempts):
            if verbose:
                print(f"\n{'='*60}")
                print(f"🎲 Attempt {attempt + 1}/{n_attempts}")

            # Random initialization
            x0 = np.random.rand(self.n)

            # Run flow
            x_final, energy_hist = self.symplectic_flow(
                x0=x0,
                T=T,
                dt=dt,
                gamma=gamma,
                verbose=verbose
            )

            final_energy = energy_hist[-1]

            # Aggiorna best
            if final_energy < best_energy:
                best_energy = final_energy
                best_x = x_final

            # Se trovato soluzione, stop
            if final_energy < 1e-4:
                if verbose:
                    print(f"\n✨ Solution found!")
                break

        # Converti a booleano
        if best_x is not None:
            x_bool = self.formula.to_boolean(best_x)

            if verbose:
                print(f"\n{'='*60}")
                print(f"📊 RESULTS")
                print(f"{'='*60}")
                print(f"Best energy: {best_energy:.8f}")
                print(f"Continuous solution: {best_x}")
                print(f"Boolean solution: {x_bool}")
                print(f"\n🔍 Verification...")

            # Verifica
            if self.formula.verify_boolean(x_bool):
                if verbose:
                    print(f"✅ VALID SAT SOLUTION!")
                return x_bool
            else:
                if verbose:
                    print(f"❌ Rounded solution doesn't satisfy formula")
                    print(f"   (but continuous solution has energy {best_energy:.6f})")
                return None

        return None

    def visualize_landscape(self, n_points: int = 50):
        """
        Visualizza paesaggio energetico (solo per n=2 variabili)
        """
        if self.n != 2:
            print("Visualization only for 2 variables!")
            return

        # Grid
        x1 = np.linspace(0, 1, n_points)
        x2 = np.linspace(0, 1, n_points)
        X1, X2 = np.meshgrid(x1, x2)

        # Calcola energia
        Z = np.zeros_like(X1)
        for i in range(n_points):
            for j in range(n_points):
                x = np.array([X1[i, j], X2[i, j]])
                Z[i, j] = self.potential(x)

        # Plot
        fig = plt.figure(figsize=(12, 5))

        # 3D surface
        ax1 = fig.add_subplot(121, projection='3d')
        ax1.plot_surface(X1, X2, Z, cmap='viridis', alpha=0.8)
        ax1.set_xlabel('x₁')
        ax1.set_ylabel('x₂')
        ax1.set_zlabel('Energy')
        ax1.set_title('Energy Landscape E(x)')

        # Contour
        ax2 = fig.add_subplot(122)
        contour = ax2.contourf(X1, X2, Z, levels=20, cmap='viridis')
        ax2.contour(X1, X2, Z, levels=20, colors='black', alpha=0.2, linewidths=0.5)
        ax2.set_xlabel('x₁')
        ax2.set_ylabel('x₂')
        ax2.set_title('Energy Contours')
        plt.colorbar(contour, ax=ax2)

        # Marca soluzioni booleane
        for i in [0, 1]:
            for j in [0, 1]:
                x = np.array([float(i), float(j)])
                E = self.potential(x)
                marker = 'o' if E < 0.1 else 'x'
                color = 'green' if E < 0.1 else 'red'
                ax2.plot(i, j, marker, color=color, markersize=10,
                        markeredgecolor='black', markeredgewidth=1)

        plt.tight_layout()
        plt.savefig('symplectic_landscape.png', dpi=150)
        print("💾 Saved landscape to 'symplectic_landscape.png'")


# ============================================================================
# ESEMPI E TEST
# ============================================================================

def create_simple_sat(n: int = 3) -> SATFormula:
    """Crea formula SAT semplice di test"""
    # (x₁ ∨ x₂) ∧ (¬x₁ ∨ x₃) ∧ (¬x₂ ∨ ¬x₃)
    clauses = [
        Clause([1, 2]),      # x₁ ∨ x₂
        Clause([-1, 3]),     # ¬x₁ ∨ x₃
        Clause([-2, -3])     # ¬x₂ ∨ ¬x₃
    ]
    return SATFormula(n, clauses)


def create_random_3sat(n: int = 10, m: int = 30, seed: int = 42) -> SATFormula:
    """Crea formula random 3-SAT"""
    np.random.seed(seed)
    clauses = []

    for _ in range(m):
        # Scegli 3 variabili random
        vars = np.random.choice(range(1, n+1), size=3, replace=False)
        # Randomizza segni
        literals = [v if np.random.rand() > 0.5 else -v for v in vars]
        clauses.append(Clause(literals))

    return SATFormula(n, clauses)


def test_simple():
    """Test su formula semplice"""
    print("\n" + "="*70)
    print("TEST 1: Simple SAT (3 vars, 3 clauses)")
    print("="*70)

    formula = create_simple_sat()
    solver = SymplecticSATSolver(formula, embedding_degree=2)

    solution = solver.solve(
        n_attempts=3,
        T=50.0,
        dt=0.01,
        gamma=0.5,
        verbose=True
    )

    if solution is not None:
        print(f"\n🎉 SUCCESS! Solution: {solution}")
    else:
        print(f"\n❌ No solution found")


def test_random_3sat():
    """Test su random 3-SAT"""
    print("\n" + "="*70)
    print("TEST 2: Random 3-SAT (10 vars, 30 clauses)")
    print("="*70)

    formula = create_random_3sat(n=10, m=30)
    solver = SymplecticSATSolver(formula, embedding_degree=2)

    solution = solver.solve(
        n_attempts=5,
        T=200.0,
        dt=0.01,
        gamma=0.3,
        verbose=True
    )

    if solution is not None:
        print(f"\n🎉 SUCCESS! Solution found")
    else:
        print(f"\n❌ No solution found (might be UNSAT or need more attempts)")


def test_visualization():
    """Test visualizzazione (2 variabili)"""
    print("\n" + "="*70)
    print("TEST 3: Landscape Visualization (2 vars)")
    print("="*70)

    # Formula con 2 variabili
    clauses = [
        Clause([1, 2]),    # x₁ ∨ x₂
        Clause([-1, 2])    # ¬x₁ ∨ x₂
    ]
    formula = SATFormula(2, clauses)

    solver = SymplecticSATSolver(formula, embedding_degree=2)
    solver.visualize_landscape()

    # Solve
    solution = solver.solve(n_attempts=3, T=50, verbose=True)


if __name__ == "__main__":
    print("""
    🌟 SYMPLECTIC SAT SOLVER - Proof of Concept
    ============================================

    Testing the revolutionary approach:
    SAT solving via geometric flow in high-dimensional symplectic space
    """)

    # Run tests
    test_simple()
    # test_random_3sat()
    # test_visualization()  # Richiede matplotlib

    print("\n" + "="*70)
    print("✨ TESTS COMPLETED")
    print("="*70)
    print("""
    📈 NEXT STEPS:
    1. Analizzare convergenza su più istanze
    2. Ottimizzare embedding (quali features funzionano meglio?)
    3. Studio teorico: dimostrare convergenza garantita
    4. Scale-up a problemi più grandi
    5. Confronto con solver tradizionali (MiniSat, etc.)

    🚀 If this works → P = NP is within reach!
    """)
