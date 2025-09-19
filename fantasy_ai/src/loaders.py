"""
Data loaders for Fantasy LaLiga JSON data.
Functions to load and normalize data from official Fantasy backend.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from .schemas import Player, TeamState, Market, RivalTeam, Position, PlayerStatus


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Parsed JSON data
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_position(position_str: str) -> Position:
    """
    Normalize position string to Position enum.
    
    Args:
        position_str: Position string from JSON
    
    Returns:
        Position enum value
    """
    position_mapping = {
        "portero": Position.PORTERO,
        "defensa": Position.DEFENSA,
        "centrocampista": Position.CENTROCAMPISTA,
        "delantero": Position.DELANTERO,
        "goalkeeper": Position.PORTERO,
        "defender": Position.DEFENSA,
        "midfielder": Position.CENTROCAMPISTA,
        "forward": Position.DELANTERO,
        "gk": Position.PORTERO,
        "def": Position.DEFENSA,
        "mid": Position.CENTROCAMPISTA,
        "att": Position.DELANTERO
    }
    
    normalized = position_str.lower().strip()
    return position_mapping.get(normalized, Position.CENTROCAMPISTA)


def normalize_player_status(status_str: str) -> PlayerStatus:
    """
    Normalize player status string to PlayerStatus enum.
    
    Args:
        status_str: Status string from JSON
    
    Returns:
        PlayerStatus enum value
    """
    status_mapping = {
        "available": PlayerStatus.AVAILABLE,
        "disponible": PlayerStatus.AVAILABLE,
        "injured": PlayerStatus.INJURED,
        "lesionado": PlayerStatus.INJURED,
        "suspended": PlayerStatus.SUSPENDED,
        "sancionado": PlayerStatus.SUSPENDED,
        "doubtful": PlayerStatus.DOUBTFUL,
        "duda": PlayerStatus.DOUBTFUL
    }
    
    normalized = status_str.lower().strip()
    return status_mapping.get(normalized, PlayerStatus.AVAILABLE)


def parse_player_from_json(player_data: Dict[str, Any]) -> Player:
    """
    Parse player data from JSON format to Player schema.
    
    Args:
        player_data: Raw player data from JSON
    
    Returns:
        Player object
    """
    # Handle different possible field names from various Fantasy APIs
    player_id = player_data.get('id') or player_data.get('player_id') or player_data.get('element')
    name = player_data.get('name') or player_data.get('web_name') or player_data.get('display_name')
    team = player_data.get('team') or player_data.get('team_name') or player_data.get('club')
    
    # Position handling
    position_raw = (
        player_data.get('position') or 
        player_data.get('element_type') or 
        player_data.get('pos') or 
        "centrocampista"
    )
    position = normalize_position(str(position_raw))
    
    # Price (handle different formats)
    price = player_data.get('price', 0.0)
    if isinstance(price, str):
        try:
            price = float(price)
        except ValueError:
            price = 0.0
    # Some APIs return price in tenths (e.g., 85 = 8.5M)
    if price > 50:
        price = price / 10.0
    
    # Points and form data
    total_points = player_data.get('total_points', 0)
    recent_points = player_data.get('recent_points', [])
    if not isinstance(recent_points, list):
        recent_points = []
    
    # Status
    status_raw = player_data.get('status', 'available')
    availability = normalize_player_status(str(status_raw))
    
    # Playing time
    minutes_played = player_data.get('minutes', 0) or player_data.get('minutes_played', 0)
    games_played = player_data.get('games_played', 0) or player_data.get('appearances', 0)
    
    # If games not provided, estimate from minutes
    if games_played == 0 and minutes_played > 0:
        games_played = max(1, minutes_played // 60)  # Estimate games from minutes
    
    # Price history
    price_history = player_data.get('price_history', [])
    if not isinstance(price_history, list):
        price_history = []
    
    # Fixtures
    next_fixtures = player_data.get('next_fixtures', [])
    if not isinstance(next_fixtures, list):
        next_fixtures = []
    
    # Calculate form if not provided
    form = player_data.get('form', 0.0)
    if form == 0.0 and recent_points:
        form = sum(recent_points) / len(recent_points)
    
    return Player(
        id=int(player_id),
        name=str(name),
        team=str(team),
        position=position,
        price=float(price),
        total_points=int(total_points),
        form=float(form),
        availability=availability,
        minutes_played=int(minutes_played),
        games_played=int(games_played),
        recent_points=recent_points,
        price_history=price_history,
        next_fixtures=next_fixtures
    )


def load_players_from_json(file_path: str) -> List[Player]:
    """
    Load players from JSON file.
    
    Args:
        file_path: Path to JSON file containing player data
    
    Returns:
        List of Player objects
    """
    data = load_json_file(file_path)
    
    # Handle different JSON structures
    players_data = []
    
    if isinstance(data, list):
        players_data = data
    elif 'players' in data:
        players_data = data['players']
    elif 'elements' in data:  # FPL-style API
        players_data = data['elements']
    elif 'data' in data:
        players_data = data['data']
    else:
        # Assume the root object contains player data
        players_data = [data]
    
    players = []
    for player_data in players_data:
        try:
            player = parse_player_from_json(player_data)
            players.append(player)
        except Exception as e:
            print(f"Warning: Failed to parse player data: {e}")
            continue
    
    return players


def load_team_state_from_json(file_path: str) -> TeamState:
    """
    Load team state from JSON file.
    
    Args:
        file_path: Path to JSON file containing team data
    
    Returns:
        TeamState object
    """
    data = load_json_file(file_path)
    
    # Extract players
    players_data = data.get('players', data.get('picks', data.get('team', [])))
    players = []
    
    for player_data in players_data:
        try:
            player = parse_player_from_json(player_data)
            players.append(player)
        except Exception as e:
            print(f"Warning: Failed to parse team player data: {e}")
            continue
    
    # Extract financial data
    bankroll = float(data.get('bankroll', data.get('bank', data.get('money_available', 0.0))))
    total_value = float(data.get('total_value', data.get('team_value', 0.0)))
    weekly_budget = float(data.get('weekly_budget', data.get('transfer_budget', 0.0)))
    transfers_made = int(data.get('transfers_made', data.get('transfers_this_week', 0)))
    
    # Calculate total value if not provided
    if total_value == 0.0 and players:
        total_value = sum(player.price for player in players)
    
    return TeamState(
        players=players,
        bankroll=bankroll,
        total_value=total_value,
        weekly_budget=weekly_budget,
        transfers_made=transfers_made
    )


def load_market_from_json(file_path: str) -> Market:
    """
    Load market state from JSON file.
    
    Args:
        file_path: Path to JSON file containing market data
    
    Returns:
        Market object
    """
    data = load_json_file(file_path)
    
    # Load available players
    available_players = load_players_from_json(file_path)
    
    # Extract trending data
    trending_up = data.get('trending_up', data.get('price_risers', []))
    trending_down = data.get('trending_down', data.get('price_fallers', []))
    most_transferred_in = data.get('most_transferred_in', data.get('transfers_in', []))
    most_transferred_out = data.get('most_transferred_out', data.get('transfers_out', []))
    
    # Ensure these are lists of integers
    def ensure_int_list(data_list):
        if not isinstance(data_list, list):
            return []
        result = []
        for item in data_list:
            try:
                if isinstance(item, dict) and 'id' in item:
                    result.append(int(item['id']))
                else:
                    result.append(int(item))
            except (ValueError, TypeError):
                continue
        return result
    
    return Market(
        available_players=available_players,
        trending_up=ensure_int_list(trending_up),
        trending_down=ensure_int_list(trending_down),
        most_transferred_in=ensure_int_list(most_transferred_in),
        most_transferred_out=ensure_int_list(most_transferred_out)
    )


def load_rivals_from_json(file_path: str) -> List[RivalTeam]:
    """
    Load rival teams from JSON file.
    
    Args:
        file_path: Path to JSON file containing rival team data
    
    Returns:
        List of RivalTeam objects
    """
    data = load_json_file(file_path)
    
    # Handle different JSON structures
    rivals_data = []
    if isinstance(data, list):
        rivals_data = data
    elif 'rivals' in data:
        rivals_data = data['rivals']
    elif 'league' in data:
        rivals_data = data['league']
    
    rivals = []
    for rival_data in rivals_data:
        try:
            team_id = str(rival_data.get('team_id', rival_data.get('id', len(rivals))))
            manager_name = str(rival_data.get('manager_name', rival_data.get('name', f'Team {team_id}')))
            
            # Extract player IDs
            players = rival_data.get('players', rival_data.get('picks', []))
            player_ids = []
            
            for player in players:
                if isinstance(player, dict):
                    player_id = player.get('id', player.get('player_id', player.get('element')))
                else:
                    player_id = player
                
                if player_id is not None:
                    player_ids.append(int(player_id))
            
            total_points = int(rival_data.get('total_points', 0))
            team_value = float(rival_data.get('team_value', 0.0))
            
            rivals.append(RivalTeam(
                team_id=team_id,
                manager_name=manager_name,
                players=player_ids,
                total_points=total_points,
                team_value=team_value
            ))
            
        except Exception as e:
            print(f"Warning: Failed to parse rival team data: {e}")
            continue
    
    return rivals


def create_sample_data_files(data_dir: str = None):
    """
    Create sample JSON data files for testing.
    
    Args:
        data_dir: Directory to create sample files (defaults to fantasy_ai/data)
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    # Sample players data
    sample_players = [
        {
            "id": 1,
            "name": "Thibaut Courtois",
            "team": "Real Madrid",
            "position": "Portero",
            "price": 6.5,
            "total_points": 85,
            "recent_points": [6, 8, 2, 9, 7],
            "status": "available",
            "minutes": 1080,
            "games_played": 12,
            "next_fixtures": ["Barcelona", "Atletico Madrid", "Valencia"]
        },
        {
            "id": 2,
            "name": "Dani Carvajal",
            "team": "Real Madrid", 
            "position": "Defensa",
            "price": 7.2,
            "total_points": 92,
            "recent_points": [8, 6, 12, 4, 9],
            "status": "available",
            "minutes": 980,
            "games_played": 11,
            "next_fixtures": ["Barcelona", "Atletico Madrid", "Valencia"]
        },
        {
            "id": 3,
            "name": "Jude Bellingham",
            "team": "Real Madrid",
            "position": "Centrocampista", 
            "price": 9.8,
            "total_points": 156,
            "recent_points": [15, 8, 12, 18, 6],
            "status": "available",
            "minutes": 1150,
            "games_played": 13,
            "next_fixtures": ["Barcelona", "Atletico Madrid", "Valencia"]
        },
        {
            "id": 4,
            "name": "Robert Lewandowski",
            "team": "Barcelona",
            "position": "Delantero",
            "price": 11.2,
            "total_points": 142,
            "recent_points": [12, 16, 4, 8, 14],
            "status": "available", 
            "minutes": 1200,
            "games_played": 14,
            "next_fixtures": ["Real Madrid", "Sevilla", "Athletic Bilbao"]
        }
    ]
    
    # Save sample players
    with open(os.path.join(data_dir, 'sample_players.json'), 'w', encoding='utf-8') as f:
        json.dump(sample_players, f, indent=2, ensure_ascii=False)
    
    # Sample team state
    sample_team = {
        "players": sample_players[:3],  # First 3 players
        "bankroll": 5.5,
        "total_value": 23.5,
        "weekly_budget": 2.0,
        "transfers_made": 1
    }
    
    with open(os.path.join(data_dir, 'sample_team.json'), 'w', encoding='utf-8') as f:
        json.dump(sample_team, f, indent=2, ensure_ascii=False)
    
    # Sample market
    sample_market = {
        "players": sample_players,
        "trending_up": [3, 4],
        "trending_down": [1],
        "most_transferred_in": [3],
        "most_transferred_out": [2]
    }
    
    with open(os.path.join(data_dir, 'sample_market.json'), 'w', encoding='utf-8') as f:
        json.dump(sample_market, f, indent=2, ensure_ascii=False)
    
    # Sample rivals
    sample_rivals = [
        {
            "team_id": "rival1",
            "manager_name": "Manager 1",
            "players": [1, 2, 4],
            "total_points": 245,
            "team_value": 85.5
        },
        {
            "team_id": "rival2", 
            "manager_name": "Manager 2",
            "players": [2, 3],
            "total_points": 267,
            "team_value": 88.2
        }
    ]
    
    with open(os.path.join(data_dir, 'sample_rivals.json'), 'w', encoding='utf-8') as f:
        json.dump(sample_rivals, f, indent=2, ensure_ascii=False)
    
    print(f"Sample data files created in: {data_dir}")


def get_data_file_path(filename: str, data_dir: str = None) -> str:
    """
    Get full path to data file.
    
    Args:
        filename: Name of the data file
        data_dir: Data directory (defaults to fantasy_ai/data)
    
    Returns:
        Full path to data file
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    return os.path.join(data_dir, filename)