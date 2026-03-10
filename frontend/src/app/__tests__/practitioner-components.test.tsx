import { describe, it, expect, jest } from '@jest/globals'
import { render, screen, fireEvent } from '@testing-library/react'
import BookingCard from '../../components/practitioner/BookingCard'
import BookingFilters from '../../components/practitioner/BookingFilters'
import PractitionerCard from '../../components/practitioner/PractitionerCard'

describe('Practitioner Components', () => {
  it('renders practitioner summary card', () => {
    render(
      <PractitionerCard
        title="Vedic Consultant"
        verificationStatus="verified"
        rating={4.8}
        sessions={120}
        languages={['English', 'Hindi']}
        specializations={['career_guidance']}
      />
    )

    expect(screen.getByText('Vedic Consultant')).toBeInTheDocument()
    expect(screen.getByText('verified')).toBeInTheDocument()
    expect(screen.getByText('career_guidance')).toBeInTheDocument()
  })

  it('calls accept and decline handlers from booking card', () => {
    const onAccept = jest.fn()
    const onDecline = jest.fn()

    render(
      <BookingCard
        id={9}
        clientName="Anaya"
        bookingDate={new Date().toISOString()}
        timeSlot="10:00"
        status="pending"
        paymentAmount={999}
        onAccept={onAccept}
        onDecline={onDecline}
      />
    )

    fireEvent.click(screen.getByText('Accept'))
    fireEvent.click(screen.getByText('Decline'))

    expect(onAccept).toHaveBeenCalledWith(9)
    expect(onDecline).toHaveBeenCalledWith(9)
  })

  it('updates booking filters', () => {
    const onStatusChange = jest.fn()
    const onPeriodChange = jest.fn()

    render(
      <BookingFilters
        status=""
        period="upcoming"
        onStatusChange={onStatusChange}
        onPeriodChange={onPeriodChange}
      />
    )

    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'confirmed' } })
    fireEvent.change(selects[1], { target: { value: 'past' } })

    expect(onStatusChange).toHaveBeenCalledWith('confirmed')
    expect(onPeriodChange).toHaveBeenCalledWith('past')
  })
})
