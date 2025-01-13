import sys


MAX_CHUNK_SIZE = 8192
resolution = 8192 * 4
zoom_levels = 6

def test1(resolution, zoom_levels):
    for zoom_level in range(zoom_levels):
        chunk_size = resolution // (2 ** zoom_level)
        num_chunks = resolution // chunk_size
        additional_num_chunks = ((resolution // (2 ** zoom_level)) // MAX_CHUNK_SIZE)
        new_num_chunks = additional_num_chunks if additional_num_chunks > 0 else num_chunks
        is_8192_each_new_num_chunks = True if additional_num_chunks > 0 else False
        
        print(f"zoom_level: {zoom_level}, \
            chunk_size: {chunk_size}, \
            num_chunks: {num_chunks} or {num_chunks}x{num_chunks}, \
            new_num_chunks: {new_num_chunks} or {new_num_chunks}x{new_num_chunks} \
            is_8192_each_new_num_chunks: {is_8192_each_new_num_chunks}, \
            additional_num_chunks: {additional_num_chunks}")

test1(resolution, zoom_levels)
print("\n\n\n")

# def test2(resolution, zoom_levels):
#     for zoom_level in range(zoom_levels):
#         chunk_size = resolution // (2 ** zoom_level)
#         num_chunks = resolution // chunk_size

#         additional_num_chunks = ((resolution // (2 ** zoom_level)) // MAX_CHUNK_SIZE)
#         new_num_chunks = additional_num_chunks if additional_num_chunks > 0 else num_chunks
#         is_8192_each_new_num_chunks = True if additional_num_chunks > 0 else False
#         new_chunk_size = chunk_size if not is_8192_each_new_num_chunks else MAX_CHUNK_SIZE
#         # for x_level in range(num_chunks):
#         #     for y_level in range(num_chunks):

#         for x_level in range(new_num_chunks):
#             for y_level in range(new_num_chunks):
#                 print(f"zoom_level: {zoom_level}, \
#                     chunk_size: {chunk_size}, \
#                     new_chunk_size: {new_chunk_size}, \
#                     x_level: {x_level}, y_level: {y_level}, \
#                     is_8192_each_new_num_chunks: {is_8192_each_new_num_chunks}")
                
#         print("\n")

# # test2(resolution, zoom_levels)
# # print("\n\n\n")

# def test3(resolution, type="overworld", zoom_levels=1):
#     """
#     generates blank white images. Each zoom_level the quality of the image doesnt increase, the number of tiles does. It will be kind of pixelated.
#     """

#     MAX_CHUNK_SIZE = 8192

#     if resolution > MAX_CHUNK_SIZE and (resolution & (resolution - 1)) != 0:
#         print(f"resolution must be divisible by 8192, and is even i.e. 8192=1x1, 16384=2x2")
#         return

#     for zoom_level in range(zoom_levels):
#         additional_num_chunks = ((resolution // (2 ** zoom_level)) // MAX_CHUNK_SIZE)
#         is_8192_each_new_num_chunks = True if additional_num_chunks > 0 else False
#         real_chunk_size = resolution // (2 ** zoom_level)
#         chunk_size = resolution // (2 ** zoom_level) if not is_8192_each_new_num_chunks else MAX_CHUNK_SIZE
#         num_chunks = additional_num_chunks if additional_num_chunks > 0 else resolution // chunk_size

#         for x_level in range(num_chunks):
#             for y_level in range(num_chunks):
#                 print(f"zoom_level: {zoom_level}, \
#                     real_chunk_size: {real_chunk_size}, \
#                     chunk_size: {chunk_size}, \
#                     x_level: {x_level}, y_level: {y_level}, \
#                     is_8192_each_new_num_chunks: {is_8192_each_new_num_chunks}")

#     for zoom_level in range(zoom_levels):
#         chunk_size = resolution // (2 ** zoom_level)
#         num_chunks = resolution // chunk_size

#         for x_level in range(num_chunks):
#             for y_level in range(num_chunks):
#                 pass

def test4(resolution, zoom_levels=4):
    MAX_CHUNK_SIZE = 8192

    if resolution > MAX_CHUNK_SIZE and (resolution & (resolution - 1)) != 0:
        print(f"resolution must be divisible by 8192, and is even i.e. 8192=1x1, 16384=2x2")
        return

    chunk_multiplier = resolution // MAX_CHUNK_SIZE

    for zoom_level in range(zoom_levels):
        base_chunk_size = resolution // (2 ** zoom_level)
        # adjusted_chunk_size = min(base_chunk_size, MAX_CHUNK_SIZE)
        adjusted_chunk_size = base_chunk_size // chunk_multiplier
        chunk_per_axis = resolution // base_chunk_size
        total_chunks = chunk_per_axis * (chunk_multiplier if chunk_multiplier > 0 else 1)

        print(f"zoom_level: {zoom_level}, \
                base_chunk_size: {base_chunk_size}, \
                adjusted_chunk_size: {adjusted_chunk_size}, \
                chunk_per_axis: {chunk_per_axis} ({chunk_per_axis*chunk_per_axis}), \
                total_chunks: {total_chunks}")

        for x_level in range(total_chunks):
            for y_level in range(total_chunks):
                pass

    # num_chunk_multiplier = resolution // MAX_CHUNK_SIZE

    # for zoom_level in range(zoom_levels):
    #         chunk_size = resolution // (2 ** zoom_level)
    #         divided_chunk_size = min(chunk_size, MAX_CHUNK_SIZE)
    #         num_chunks = (resolution // chunk_size) * (num_chunk_multiplier if num_chunk_multiplier > 0 else 1)
    #         print(f"zoom_level: {zoom_level}, \
    #             chunk_size: {chunk_size}, \
    #             num_chunks: {num_chunks}, \
    #             divided_chunk_size: {divided_chunk_size}")
    #         for x_level in range(num_chunks):
    #             for y_level in range(num_chunks):
    #                 pass

test4(resolution, zoom_levels)
print("\n\n\n")

















def final_test(resolution, zoom_levels):
    MAX_CHUNK_SIZE = 8192

    if resolution > MAX_CHUNK_SIZE and (resolution & (resolution - 1)) != 0:
        print(f"resolution must be divisible by 8192, and is even i.e. 8192=1x1, 16384=2x2")
        return

    chunk_multiplier = max(1, resolution // MAX_CHUNK_SIZE)

    for zoom_level in range(zoom_levels):
        zoom_level = int(zoom_level)
        base_chunk_size = resolution // (2 ** zoom_level)
        # adjusted_chunk_size = min(base_chunk_size, MAX_CHUNK_SIZE)
        adjusted_chunk_size = base_chunk_size // chunk_multiplier
        chunk_per_axis = resolution // base_chunk_size
        total_chunks = chunk_per_axis * chunk_multiplier

        base_chunk_size_multiplier = max(1, base_chunk_size // MAX_CHUNK_SIZE)

        print(f"zoom_level: {zoom_level}, \
                base_chunk_size: {base_chunk_size}, \
                adjusted_chunk_size: {adjusted_chunk_size}, \
                chunk_per_axis: {chunk_per_axis} ({chunk_per_axis * chunk_per_axis}) / {((chunk_per_axis * chunk_per_axis) * base_chunk_size_multiplier) // 2} ({(chunk_per_axis * chunk_per_axis) * base_chunk_size_multiplier}), \
                base_chunk_size_multiplier: {base_chunk_size_multiplier}")
        
final_test(resolution, zoom_levels)