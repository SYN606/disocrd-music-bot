from __future__ import annotations
import wavelink


class QueueManager:

    @staticmethod
    async def add_track(player: wavelink.Player, track: wavelink.Playable):
        player.queue.put(track)

    @staticmethod
    async def add_playlist(player: wavelink.Player,
                           playlist: wavelink.Playlist):
        for track in playlist.tracks:
            player.queue.put(track)

    @staticmethod
    async def get_next(player: wavelink.Player):
        if player.queue.is_empty:
            return None
        return await player.queue.get_wait()

    @staticmethod
    def clear(player: wavelink.Player):
        player.queue.clear()

    @staticmethod
    def count(player: wavelink.Player) -> int:
        return player.queue.count

    @staticmethod
    def remove_track(player: wavelink.Player,
                     track: wavelink.Playable) -> bool:
        queue_list = list(player.queue)
        if track not in queue_list:
            return False
        queue_list.remove(track)
        player.queue.clear()
        for item in queue_list:
            player.queue.put(item)

        return True
