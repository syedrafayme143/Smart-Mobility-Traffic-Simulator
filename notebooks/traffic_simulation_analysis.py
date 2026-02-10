import os
import sys
import json
import csv
from typing import Dict, List, Tuple
from datetime import datetime
import traci
from sumolib import checkBinary

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    PLOTTING_AVAILABLE = True
except ImportError:
    print("⚠️  Matplotlib not available. Visualization features disabled.")
    PLOTTING_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("⚠️  Pandas not available. Data export features limited.")
    PANDAS_AVAILABLE = False


class SUMOTrafficSimulator:
    """
     SUMO Traffic Simulator with analytics and visualization
    """
    
    def __init__(self, config_path: str, gui_mode: bool = False):
        """
        Initialize the simulator
        
        Args:
            config_path: Path to SUMO configuration file
            gui_mode: Whether to run with GUI (True) or headless (False)
        """
        self.config_path = config_path
        self.gui_mode = gui_mode
        self.edge_counts = {}
        self.edge_speeds = {}
        self.edge_occupancy = {}
        self.vehicle_travel_times = {}
        self.simulation_steps = 0
        
    def setup_sumo_environment(self, sumo_home: str = None):
        """
        Configure SUMO environment variables
        
        Args:
            sumo_home: Path to SUMO installation (auto-detect if None)
        """
        if sumo_home:
            os.environ['SUMO_HOME'] = sumo_home
        elif 'SUMO_HOME' not in os.environ:
            # Try common installation paths
            common_paths = [
                "C:/Program Files (x86)/Eclipse/Sumo",
                "/usr/share/sumo",
                "/usr/local/share/sumo"
            ]
            for path in common_paths:
                if os.path.exists(path):
                    os.environ['SUMO_HOME'] = path
                    break
            else:
                raise EnvironmentError(
                    "SUMO_HOME not set and could not auto-detect SUMO installation"
                )
        
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        if tools not in sys.path:
            sys.path.append(tools)
            
        print(f"✅ SUMO_HOME configured: {os.environ['SUMO_HOME']}")
    
    def run_simulation(self) -> Dict[str, List[float]]:
        """
        Execute the SUMO simulation and collect metrics
        
        Returns:
            Dictionary containing edge-wise traffic metrics
        """
        try:
            # Select binary
            sumoBinary = checkBinary('sumo-gui' if self.gui_mode else 'sumo')
            
            # Start TraCI
            print(f"\n🚀 Starting SUMO simulation...")
            print(f"   Configuration: {self.config_path}")
            print(f"   Mode: {'GUI' if self.gui_mode else 'Headless'}\n")
            
            traci.start([sumoBinary, "-c", self.config_path])
            
            # Main simulation loop
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                self._collect_step_data()
                self.simulation_steps += 1
                
                # Progress indicator (every 50 steps)
                if self.simulation_steps % 50 == 0:
                    print(f"⏱️  Step {self.simulation_steps}: "
                          f"{traci.simulation.getMinExpectedNumber()} vehicles remaining")
            
            # Close TraCI
            traci.close()
            
            print(f"\n✅ Simulation completed: {self.simulation_steps} steps\n")
            
            return self._calculate_metrics()
            
        except traci.exceptions.FatalTraCIError as e:
            print(f"❌ TraCI Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise
    
    def _collect_step_data(self):
        """
        Collect traffic data for current simulation step
        """
        for edge_id in traci.edge.getIDList():
            # Vehicle count
            vehicle_count = traci.edge.getLastStepVehicleNumber(edge_id)
            if edge_id not in self.edge_counts:
                self.edge_counts[edge_id] = []
            self.edge_counts[edge_id].append(vehicle_count)
            
            # Average speed
            avg_speed = traci.edge.getLastStepMeanSpeed(edge_id)
            if edge_id not in self.edge_speeds:
                self.edge_speeds[edge_id] = []
            self.edge_speeds[edge_id].append(avg_speed)
            
            # Occupancy
            occupancy = traci.edge.getLastStepOccupancy(edge_id)
            if edge_id not in self.edge_occupancy:
                self.edge_occupancy[edge_id] = []
            self.edge_occupancy[edge_id].append(occupancy)
    
    def _calculate_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate aggregate metrics from collected data
        
        Returns:
            Dictionary with calculated metrics per edge
        """
        metrics = {}
        
        for edge_id in self.edge_counts.keys():
            metrics[edge_id] = {
                'avg_vehicles': sum(self.edge_counts[edge_id]) / len(self.edge_counts[edge_id]),
                'max_vehicles': max(self.edge_counts[edge_id]),
                'avg_speed': sum(self.edge_speeds[edge_id]) / len(self.edge_speeds[edge_id]),
                'avg_occupancy': sum(self.edge_occupancy[edge_id]) / len(self.edge_occupancy[edge_id])
            }
        
        return metrics
    
    def print_results(self, metrics: Dict[str, Dict[str, float]]):
        """
        Display simulation results in formatted table
        
        Args:
            metrics: Calculated metrics dictionary
        """
        print("=" * 80)
        print("📊 SIMULATION RESULTS")
        print("=" * 80)
        
        # Filter and sort by average vehicles
        significant_edges = {
            k: v for k, v in metrics.items() 
            if not k.startswith(':') and v['avg_vehicles'] > 0.1
        }
        sorted_edges = sorted(
            significant_edges.items(), 
            key=lambda x: x[1]['avg_vehicles'], 
            reverse=True
        )
        
        print(f"\n{'Edge ID':<15} {'Avg Vehicles':<15} {'Max Vehicles':<15} "
              f"{'Avg Speed (m/s)':<18} {'Avg Occupancy (%)':<18}")
        print("-" * 80)
        
        for edge_id, data in sorted_edges:
            print(f"{edge_id:<15} {data['avg_vehicles']:<15.2f} "
                  f"{data['max_vehicles']:<15.0f} {data['avg_speed']:<18.2f} "
                  f"{data['avg_occupancy'] * 100:<18.2f}")
        
        print("\n" + "=" * 80)
        
        # Summary statistics
        all_avg_vehicles = [v['avg_vehicles'] for v in significant_edges.values()]
        print(f"\n📈 SUMMARY STATISTICS")
        print(f"   Total edges analyzed: {len(significant_edges)}")
        print(f"   Highest density edge: {sorted_edges[0][0]} "
              f"({sorted_edges[0][1]['avg_vehicles']:.2f} vehicles)")
        print(f"   Network average: {sum(all_avg_vehicles) / len(all_avg_vehicles):.2f} vehicles")
        print(f"   Total simulation steps: {self.simulation_steps}")
        print()
    
    def export_to_csv(self, metrics: Dict[str, Dict[str, float]], filename: str = None):
        """
        Export results to CSV file
        
        Args:
            metrics: Calculated metrics dictionary
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['edge_id', 'avg_vehicles', 'max_vehicles', 
                             'avg_speed', 'avg_occupancy']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for edge_id, data in metrics.items():
                    writer.writerow({
                        'edge_id': edge_id,
                        'avg_vehicles': data['avg_vehicles'],
                        'max_vehicles': data['max_vehicles'],
                        'avg_speed': data['avg_speed'],
                        'avg_occupancy': data['avg_occupancy']
                    })
            
            print(f"💾 Results exported to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to export CSV: {e}")
    
    def export_to_json(self, metrics: Dict[str, Dict[str, float]], filename: str = None):
        """
        Export results to JSON file
        
        Args:
            metrics: Calculated metrics dictionary
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.json"
        
        try:
            export_data = {
                'simulation_info': {
                    'config_file': self.config_path,
                    'total_steps': self.simulation_steps,
                    'timestamp': datetime.now().isoformat()
                },
                'edge_metrics': metrics
            }
            
            with open(filename, 'w') as jsonfile:
                json.dump(export_data, jsonfile, indent=2)
            
            print(f"💾 Results exported to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to export JSON: {e}")
    
    def visualize_results(self, metrics: Dict[str, Dict[str, float]]):
        """
        Create visualization plots of simulation results
        
        Args:
            metrics: Calculated metrics dictionary
        """
        if not PLOTTING_AVAILABLE:
            print("⚠️  Matplotlib not available. Skipping visualization.")
            return
        
        # Filter significant edges
        significant_edges = {
            k: v for k, v in metrics.items() 
            if not k.startswith(':') and v['avg_vehicles'] > 0.1
        }
        
        # Sort by average vehicles
        sorted_edges = sorted(
            significant_edges.items(), 
            key=lambda x: x[1]['avg_vehicles'], 
            reverse=True
        )
        
        edge_names = [e[0] for e in sorted_edges]
        avg_vehicles = [e[1]['avg_vehicles'] for e in sorted_edges]
        avg_speeds = [e[1]['avg_speed'] for e in sorted_edges]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Average Vehicles per Edge
        colors = ['#e74c3c' if v > 3 else '#f39c12' if v > 2 else '#2ecc71' 
                  for v in avg_vehicles]
        ax1.barh(edge_names, avg_vehicles, color=colors, alpha=0.7)
        ax1.set_xlabel('Average Vehicles', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Edge ID', fontsize=12, fontweight='bold')
        ax1.set_title('Traffic Density: Average Vehicles per Edge', 
                      fontsize=14, fontweight='bold', pad=20)
        ax1.grid(axis='x', alpha=0.3)
        
        # Add legend
        high_patch = mpatches.Patch(color='#e74c3c', alpha=0.7, label='High (>3 veh)')
        medium_patch = mpatches.Patch(color='#f39c12', alpha=0.7, label='Medium (2-3 veh)')
        low_patch = mpatches.Patch(color='#2ecc71', alpha=0.7, label='Low (<2 veh)')
        ax1.legend(handles=[high_patch, medium_patch, low_patch], loc='lower right')
        
        # Plot 2: Average Speed per Edge
        ax2.barh(edge_names, avg_speeds, color='#3498db', alpha=0.7)
        ax2.set_xlabel('Average Speed (m/s)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Edge ID', fontsize=12, fontweight='bold')
        ax2.set_title('Traffic Flow: Average Speed per Edge', 
                      fontsize=14, fontweight='bold', pad=20)
        ax2.grid(axis='x', alpha=0.3)
        ax2.axvline(x=13.89, color='red', linestyle='--', linewidth=2, 
                    label='Speed Limit (13.89 m/s)')
        ax2.legend()
        
        plt.tight_layout()
        
        # Save figure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_visualization_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Visualization saved to: {filename}")
        
        plt.show()


def main():
    """
    Main execution function
    """
    # Configuration
    CONFIG_PATH = "simulation/sumo_config.sumocfg"
    SUMO_HOME = "C:/Program Files (x86)/Eclipse/Sumo"  # Adjust as needed
    
    # Create simulator instance
    simulator = SUMOTrafficSimulator(
        config_path=CONFIG_PATH,
        gui_mode=False  # Set True to see visualization
    )
    
    # Setup environment
    simulator.setup_sumo_environment(SUMO_HOME)
    
    # Run simulation
    metrics = simulator.run_simulation()
    
    # Display results
    simulator.print_results(metrics)
    
    # Export results
    simulator.export_to_csv(metrics)
    simulator.export_to_json(metrics)
    
    # Visualize (if matplotlib available)
    simulator.visualize_results(metrics)
    
    print("\n✨ Analysis complete!\n")


if __name__ == "__main__":
    main()
