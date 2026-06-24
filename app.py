import streamlit as st
from datetime import datetime, time, timedelta

st.set_page_config(page_title="Compensatory Rest Calculator")

THRESHOLD = timedelta(hours=1, minutes=30)
REST_REQUIRED = timedelta(hours=9)

WINDOW_START = time(0, 0)
WINDOW_END = time(5, 0)


def combine(date, t):
    return datetime.combine(date, t)


def get_window(date):
    start = combine(date, WINDOW_START)
    end = combine(date, WINDOW_END)
    return start, end


def overlap_interval(start1, end1, start2, end2):
    start = max(start1, start2)
    end = min(end1, end2)

    if end <= start:
        return None

    return start, end


def qualifying_segment(start, end, window_start, window_end):
    overlap = overlap_interval(start, end, window_start, window_end)

    if not overlap:
        return None

    seg_start, seg_end = overlap

    if seg_end - seg_start >= THRESHOLD:
        return seg_start, seg_end

    return None


def find_latest_qualifying(efforts, window_start, window_end):

    qualifying = []

    for start, end in efforts:

        segment = qualifying_segment(start, end, window_start, window_end)

        if segment:
            qualifying.append((start, end, segment))

    if not qualifying:
        return None

    qualifying.sort(key=lambda x: x[1])

    return qualifying[-1]


st.title("Compensatory Rest Calculator")

st.write(
    "Calculate earliest allowed start time after night work between 00:00–05:00."
)

shift_date = st.date_input("Date of next regular shift")
regular_start = st.time_input("Regular shift start", value=time(8, 0))

st.header("Night work efforts")

if "efforts" not in st.session_state:
    st.session_state.efforts = []

if st.button("Add work effort"):
    st.session_state.efforts.append({"start": time(0, 0), "end": time(1, 30)})

for i, effort in enumerate(st.session_state.efforts):

    col1, col2, col3 = st.columns([3,3,1])

    with col1:
        effort["start"] = st.time_input(
            f"Start #{i+1}",
            value=effort["start"],
            key=f"s{i}"
        )

    with col2:
        effort["end"] = st.time_input(
            f"End #{i+1}",
            value=effort["end"],
            key=f"e{i}"
        )

    with col3:
        if st.button("Remove", key=f"r{i}"):
            st.session_state.efforts.pop(i)
            st.rerun()


if st.button("Calculate"):

    night_date = shift_date - timedelta(days=1)

    window_start, window_end = get_window(shift_date)

    efforts = []

    for e in st.session_state.efforts:

        start = combine(night_date, e["start"])
        end = combine(night_date, e["end"])

        if end <= start:
            end += timedelta(days=1)

        efforts.append((start, end))

    latest = find_latest_qualifying(efforts, window_start, window_end)

    regular_start_dt = combine(shift_date, regular_start)

    st.subheader("Result")

    if not latest:

        st.warning("No qualifying work effort (≥1.5h within 00:00–05:00).")
        st.write(f"Regular start applies: {regular_start_dt.time()}")

    else:

        start, end, segment = latest
        rest_start = end
        earliest_start = rest_start + REST_REQUIRED

        seg_start, seg_end = segment

        st.write("Qualifying segment inside 00:00–05:00:")
        st.write(f"{seg_start} → {seg_end}")

        st.write("Last qualifying work effort:")
        st.write(f"{start} → {end}")

        st.write("Rest period:")
        st.write(f"{rest_start} → {earliest_start}")

        if earliest_start > regular_start_dt:

            st.success(
                f"Earliest allowed start time: {earliest_start.strftime('%H:%M')}"
            )

        else:

            st.success(
                f"Regular start time applies: {regular_start_dt.strftime('%H:%M')}"
            )
