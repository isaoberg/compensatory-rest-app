import streamlit as st
from datetime import datetime, date

# -------------------------------------------------
# Inställningar
# -------------------------------------------------

st.set_page_config(
    page_title="Dygnsvila – beräkningsverktyg",
    layout="centered"
)

TRÖSKEL = 90        # minuter
KRÄVD_VILA = 540    # 9 timmar

FÖNSTER_START = 0
FÖNSTER_SLUT = 300  # 05:00


# -------------------------------------------------
# Hjälpfunktioner
# -------------------------------------------------

def tolka_tid(t):

    try:
        dt = datetime.strptime(t, "%H:%M")
        minuter = dt.hour * 60 + dt.minute

        if minuter >= 720:
            minuter -= 1440

        return minuter

    except:
        return None


def klipp_till_fönster(start, slut):

    start = max(start, FÖNSTER_START)
    slut = min(slut, FÖNSTER_SLUT)

    if slut <= start:
        return None

    return start, slut


def minuter_till_tid(m):

    h = m // 60
    m = m % 60

    if h < 0:
        h += 24

    return f"{h:02}:{m:02}"


# -------------------------------------------------
# Titel
# -------------------------------------------------

st.title("Beräkning av kompenserad dygnsvila")

st.markdown(
"""
Beräknar **tidigaste tillåtna starttid** efter nattliga störningar.

Regler:

• Omfattande störningar räknas endast mellan **00:00–05:00**  
• Omfattande störning = störning **≥ 1 timme 30 minuter**  
• Vid flera störningar samma natt krävs att minst **en störning ≥ 1 timme 30 minuter**  
• Det är den **aktiva tiden** på störningarna som räknas  
• Kompenserad vila räknas från **sista störningen**  
• Vila mellan störningar räknas av från de **9 timmar** som ska kompenseras.
"""
)

st.divider()

# -------------------------------------------------
# Ordinarie arbetspass
# -------------------------------------------------

st.header("Ordinarie arbetspass")

skiftdatum = st.date_input(
    "Datum för nästa arbetspass",
    value=date.today()
)

ordinarie_start_str = st.text_input(
    "Ordinarie starttid (HH:MM)",
    value="07:00"
)

ordinarie_start = tolka_tid(ordinarie_start_str)

if ordinarie_start is None:
    st.error("Starttiden måste anges som HH:MM")
    st.stop()

st.divider()

# -------------------------------------------------
# Störningar
# -------------------------------------------------

st.header("Störningar under natten")

if "störningar" not in st.session_state:
    st.session_state.störningar = []

if st.button("➕ Lägg till störning"):
    st.session_state.störningar.append({"start": "00:00", "slut": "01:00"})


for i, störning in enumerate(st.session_state.störningar):

    col1, col2, col3 = st.columns([3,3,1])

    with col1:
        störning["start"] = st.text_input(
            f"Start #{i+1} (HH:MM)",
            value=störning["start"],
            key=f"s{i}"
        )

    with col2:
        störning["slut"] = st.text_input(
            f"Slut #{i+1} (HH:MM)",
            value=störning["slut"],
            key=f"e{i}"
        )

    with col3:
        if st.button("Ta bort", key=f"r{i}"):
            st.session_state.störningar.pop(i)
            st.rerun()

st.divider()

# -------------------------------------------------
# Beräkning
# -------------------------------------------------

if st.button("Beräkna tidigaste starttid"):

    störningar = []

    for s in st.session_state.störningar:

        start = tolka_tid(s["start"])
        slut = tolka_tid(s["slut"])

        if start is None or slut is None:
            st.error("Tider måste anges som HH:MM")
            st.stop()

        if slut <= start:
            slut += 1440

        klippt = klipp_till_fönster(start, slut)

        if klippt:
            störningar.append(klippt)

    störningar.sort()

    if not störningar:
        st.warning("Ingen störning inträffade mellan 00:00 och 05:00.")
        st.stop()

    kvalificerar = any((e - s) >= TRÖSKEL for s, e in störningar)

    if not kvalificerar:
        st.warning("Ingen störning är minst 1 timme och 30 minuter.")
        st.write(f"Ordinarie starttid gäller: **{ordinarie_start_str}**")
        st.stop()

    vila_mellan = 0

    for i in range(len(störningar) - 1):

        slut_förra = störningar[i][1]
        start_nästa = störningar[i + 1][0]

        paus = start_nästa - slut_förra

        if paus > 0:
            vila_mellan += paus

    sista_slut = störningar[-1][1]

    kvarvarande_vila = KRÄVD_VILA - vila_mellan

    if kvarvarande_vila < 0:
        kvarvarande_vila = 0

    tidigaste_start = sista_slut + kvarvarande_vila

    st.subheader("Resultat")

    col1, col2 = st.columns(2)

    col1.metric(
        "Vila mellan störningar",
        f"{vila_mellan} min"
    )

    col2.metric(
        "Kvarvarande vila",
        f"{kvarvarande_vila} min"
    )

    st.divider()

    if tidigaste_start > ordinarie_start:

        st.success(
            f"Tidigaste tillåtna starttid: **{minuter_till_tid(tidigaste_start)}**"
        )

    else:

        st.success(
            f"Ordinarie starttid gäller: **{ordinarie_start_str}**"
        )
